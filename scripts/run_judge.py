"""Score a run with the Gemini judge.

Usage (from repo root):
    .venv/bin/python scripts/run_judge.py RUN_NAME [--no-photo-source] [--research DIR]
--research DIR: the research notes the judge treats as sources (default data/research).
Judge each run against the notes its pipeline saw; the baseline uses data/research.

Both the before and the after run are judged against the SAME sources:
catalog, store facts, the cached research notes (data/research/) and the photo.
The baseline never saw the research notes, so this is generous to the baseline:
it can only make the measured improvement smaller, never larger.

Writes runs/RUN_NAME/judge.jsonl and runs/RUN_NAME/scores.json
"""
import json
import pathlib
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, ".")
from storefront_agents import judge, llm  # noqa: E402
from storefront_agents.catalog import load_catalog  # noqa: E402


def main():
    run_name = sys.argv[1]
    photo_is_source = "--no-photo-source" not in sys.argv
    research_dir = pathlib.Path(sys.argv[sys.argv.index("--research") + 1]) if "--research" in sys.argv else pathlib.Path("data/research")
    run_dir = pathlib.Path("runs") / run_name
    catalog = {p["id"]: p for p in load_catalog()}
    rows = [json.loads(line) for line in open(run_dir / "outputs.jsonl", encoding="utf-8")]

    def notes(pid):
        f = research_dir / f"{pid}.json"
        return json.loads(f.read_text())["notes"] if f.exists() else []

    def one(r):
        if "output" not in r:
            return {"id": r["id"], "error": r.get("error", "no output")}
        try:
            s = judge.score(catalog[r["id"]], r["output"], notes(r["id"]), photo_is_source)
            return {"id": r["id"], "group": r["group"], "status": r.get("status", "n/a"), "scores": s}
        except Exception as e:
            return {"id": r["id"], "error": str(e)[:300]}

    with ThreadPoolExecutor(max_workers=3) as pool:
        judged = list(pool.map(one, rows))
    with open(run_dir / "judge.jsonl", "w", encoding="utf-8") as f:
        for j in judged:
            f.write(json.dumps(j, ensure_ascii=False) + "\n")

    ok = [j for j in judged if "scores" in j]
    per_criterion = {c: round(sum(j["scores"][c]["pass"] for j in ok) / len(ok), 3) for c in judge.CRITERIA} if ok else {}
    summary = {
        "run": run_name,
        "judged": len(ok),
        "errors": len(judged) - len(ok),
        "photo_is_source": photo_is_source,
        "research_dir": str(research_dir),
        "pass_rate_by_criterion": per_criterion,
        "truth_all_pass": sum(all(j["scores"][c]["pass"] for c in judge.TRUTH) for j in ok),
        "products_pass_bar5": sum(judge.product_passes(j["scores"], 5) for j in ok),
        "products_pass_bar4": sum(judge.product_passes(j["scores"], 4) for j in ok),
        "judge_usage": llm.USAGE.get("judge"),
    }
    (run_dir / "scores.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
