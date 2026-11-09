"""Block 4/5: run the agent pipeline on products and save everything.

Usage (from repo root):
    .venv/bin/python scripts/run_pipeline.py RUN_NAME [ITEM_ID ...]
Writes runs/RUN_NAME/outputs.jsonl and runs/RUN_NAME/run.json
With ITEM_IDs and an existing run: replaces only those rows and logs the re-run
in run.json under "reruns" (the first run's summary stays as it was).
"""
import json
import pathlib
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

sys.path.insert(0, ".")
from storefront_agents import llm, skills  # noqa: E402
from storefront_agents.catalog import load_catalog  # noqa: E402
from storefront_agents.pipeline import MAX_REVISIONS, run_product  # noqa: E402


def write_rows(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    args = sys.argv[1:]
    reason = None
    if "--reason" in args:
        i = args.index("--reason")
        reason = args[i + 1]
        del args[i:i + 2]
    run_name, only = args[0], set(args[1:])
    out_dir = pathlib.Path("runs") / run_name
    out_dir.mkdir(parents=True, exist_ok=True)
    raw = {}
    for line in open("data/abo/selected_listings.jsonl", encoding="utf-8"):
        r = json.loads(line)
        raw[r["item_id"]] = r
    catalog = [p for p in load_catalog() if not only or p["id"] in only]
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")

    def safe(p):
        try:
            return run_product(p, raw[p["id"]])
        except Exception as e:
            return {"id": p["id"], "name": p["name"], "group": p["group"], "status": "error", "error": str(e)[:400]}

    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(safe, catalog))
    out_file, run_file = out_dir / "outputs.jsonl", out_dir / "run.json"
    if only and out_file.exists():  # re-run of a few products: merge, keep the rest
        new = {r["id"]: r for r in results}
        rows = [json.loads(line) for line in open(out_file, encoding="utf-8")]
        merged = [new.pop(r["id"], r) for r in rows] + list(new.values())
        write_rows(out_file, merged)
        summary = json.loads(run_file.read_text())
        summary["status"] = dict(Counter(r["status"] for r in merged))
        summary["revised"] = sum(1 for r in merged if r.get("revisions"))
        summary.setdefault("reruns", []).append({
            "ids": sorted(only),
            "started_utc": started,
            "reason": reason,
            "status": {r["id"]: r["status"] for r in results},
            "skills": {s["name"]: s["version"] for s in skills.all_skills()},
            "usage_by_agent": llm.USAGE,
        })
        run_file.write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary["reruns"][-1], indent=2))
        return
    write_rows(out_file, results)
    summary = {
        "run": run_name,
        "model": llm.MODEL,
        "started_utc": started,
        "products": len(results),
        "status": dict(Counter(r["status"] for r in results)),
        "revised": sum(1 for r in results if r.get("revisions")),
        "max_revisions": MAX_REVISIONS,
        "skills": {s["name"]: s["version"] for s in skills.all_skills()},
        "usage_by_agent": llm.USAGE,
    }
    run_file.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
