"""Block 3: run ONE plain prompt on every product. This is the "before".

Same inputs as the final pipeline (product data, photo, store facts), but no
agents, no skill library, no Search grounding, no Validator.

Usage (from repo root):  .venv/bin/python scripts/run_baseline.py [--reason TEXT] [ITEM_ID ...]
Writes: runs/baseline-v1/outputs.jsonl and runs/baseline-v1/run.json
With ITEM_IDs: re-runs only those products, replaces their rows, and logs the
re-run in run.json under "reruns" (the first run's summary stays as it was).
"""
import json
import pathlib
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

sys.path.insert(0, ".")
from google import genai  # noqa: E402
from google.genai import types  # noqa: E402

from storefront_agents.catalog import load_catalog  # noqa: E402

PROJECT = "storefront-agents-4128"
LOCATION = "global"
MODEL = "gemini-3.8-flash"
PROMPT_FILE = "prompts/baseline_v1.md"
OUT_DIR = pathlib.Path("runs/baseline-v1")


def store_facts_text():
    text = pathlib.Path("skills/store-facts.md").read_text()
    return text.split("---", 2)[2].strip() if text.startswith("---") else text  # drop front matter


def product_json(p):
    return json.dumps({k: p[k] for k in ("name", "group", "bullets", "description")}, indent=2, ensure_ascii=False)


def run_one(client, template, facts, p):
    prompt = template.replace("{store_facts}", facts).replace("{product_json}", product_json(p))
    image = types.Part.from_bytes(data=pathlib.Path(p["image"]).read_bytes(), mime_type="image/jpeg")
    t0 = time.time()
    for attempt in range(3):
        try:
            resp = client.models.generate_content(
                model=MODEL,
                contents=[image, prompt],
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
            break
        except Exception as e:  # retry transient errors
            if attempt == 2:
                return {"id": p["id"], "error": f"{type(e).__name__}: {e}"[:300]}
            time.sleep(5 * (attempt + 1))
    u = resp.usage_metadata
    try:
        output = json.loads(resp.text)
    except Exception:
        output = {"_unparsed": resp.text}
    return {
        "id": p["id"],
        "name": p["name"],
        "group": p["group"],
        "output": output,
        "usage": {
            "input_tokens": u.prompt_token_count,
            "output_tokens": u.candidates_token_count,
            "thinking_tokens": getattr(u, "thoughts_token_count", None),
        },
        "seconds": round(time.time() - t0, 1),
    }


def write_rows(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)
    template = pathlib.Path(PROMPT_FILE).read_text()
    facts = store_facts_text()
    args = sys.argv[1:]
    reason = None
    if "--reason" in args:
        i = args.index("--reason")
        reason = args[i + 1]
        del args[i:i + 2]
    only = set(args)
    catalog = [p for p in load_catalog() if not only or p["id"] in only]
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda p: run_one(client, template, facts, p), catalog))
    out_file, run_file = OUT_DIR / "outputs.jsonl", OUT_DIR / "run.json"
    ok = [r for r in results if "error" not in r]
    if only and out_file.exists():  # re-run of a few products: merge, keep the rest
        new = {r["id"]: r for r in results}
        rows = [json.loads(line) for line in open(out_file, encoding="utf-8")]
        merged = [new.pop(r["id"], r) for r in rows] + list(new.values())
        write_rows(out_file, merged)
        summary = json.loads(run_file.read_text())
        summary["errors"] = sum(1 for r in merged if "error" in r)
        summary.setdefault("reruns", []).append({
            "ids": sorted(only),
            "started_utc": started,
            "reason": reason,
            "errors": len(results) - len(ok),
            "input_tokens": sum(r["usage"]["input_tokens"] or 0 for r in ok),
            "output_tokens": sum(r["usage"]["output_tokens"] or 0 for r in ok),
            "thinking_tokens": sum(r["usage"]["thinking_tokens"] or 0 for r in ok),
        })
        run_file.write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary["reruns"][-1], indent=2))
        return
    write_rows(out_file, results)
    summary = {
        "run": "baseline-v1",
        "model": MODEL,
        "prompt_file": PROMPT_FILE,
        "started_utc": started,
        "products": len(results),
        "errors": len(results) - len(ok),
        "input_tokens": sum(r["usage"]["input_tokens"] or 0 for r in ok),
        "output_tokens": sum(r["usage"]["output_tokens"] or 0 for r in ok),
        "thinking_tokens": sum(r["usage"]["thinking_tokens"] or 0 for r in ok),
    }
    run_file.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
