"""Block 4/5: run the agent pipeline on products and save everything.

Usage (from repo root):
    .venv/bin/python scripts/run_pipeline.py RUN_NAME [ITEM_ID ...]
Writes runs/RUN_NAME/outputs.jsonl and runs/RUN_NAME/run.json
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


def main():
    run_name, only = sys.argv[1], set(sys.argv[2:])
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
    with open(out_dir / "outputs.jsonl", "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
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
    (out_dir / "run.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
