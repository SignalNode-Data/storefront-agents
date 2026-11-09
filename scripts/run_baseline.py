"""Block 3: run ONE plain prompt on every product. This is the "before".

Same inputs as the final pipeline (product data, photo, store facts), but no
agents, no skill library, no Search grounding, no Validator.

Usage (from repo root):  .venv/bin/python scripts/run_baseline.py
Writes: runs/baseline-v1/outputs.jsonl and runs/baseline-v1/run.json
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


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)
    template = pathlib.Path(PROMPT_FILE).read_text()
    facts = store_facts_text()
    catalog = load_catalog()
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda p: run_one(client, template, facts, p), catalog))
    with open(OUT_DIR / "outputs.jsonl", "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    ok = [r for r in results if "error" not in r]
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
    (OUT_DIR / "run.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
