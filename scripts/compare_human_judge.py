"""Compare the candidate's blind hand-scores with the Gemini judge, criterion by criterion.

Usage (from repo root):
    .venv/bin/python scripts/compare_human_judge.py [SCORES_CSV]
Default SCORES_CSV: evals/hand-scoring/scores-corrected.csv
Reads evals/hand-scoring/key.json and runs/<run>/judge.jsonl.
Writes evals/hand-scoring/agreement.json
"""
import csv
import json
import pathlib
import sys

sys.path.insert(0, ".")
from storefront_agents.judge import CRITERIA, product_passes  # noqa: E402

HS = pathlib.Path("evals/hand-scoring")


def main():
    scores_csv = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HS / "scores-corrected.csv"
    human = {r["item"]: r for r in csv.DictReader(open(scores_csv, encoding="utf-8"))}
    key = json.loads((HS / "key.json").read_text())
    judged = {}
    for run in {k["run"] for k in key}:
        for line in open(f"runs/{run}/judge.jsonl", encoding="utf-8"):
            j = json.loads(line)
            judged[(run, j["id"])] = j["scores"]

    items, per_c = [], {c: {"agree": 0, "n": 0, "disagreements": []} for c in CRITERIA}
    for k in key:
        h, j = human[k["item"]], judged[(k["run"], k["pid"])]
        h_scores = {c: {"pass": h[c] == "pass"} for c in CRITERIA}
        for c in CRITERIA:
            per_c[c]["n"] += 1
            if h_scores[c]["pass"] == j[c]["pass"]:
                per_c[c]["agree"] += 1
            else:
                per_c[c]["disagreements"].append({
                    "item": k["item"], "run": k["run"], "pid": k["pid"],
                    "human": h[c], "judge": "pass" if j[c]["pass"] else "fail",
                    "judge_reason": j[c].get("reason", ""),
                })
        items.append({
            "item": k["item"], "run": k["run"], "pid": k["pid"],
            "human_pass_bar5": product_passes(h_scores, 5),
            "judge_pass_bar5": product_passes(j, 5),
        })

    total_agree = sum(v["agree"] for v in per_c.values())
    total_n = sum(v["n"] for v in per_c.values())
    out = {
        "scores_file": str(scores_csv),
        "items": len(items),
        "agreement_overall": round(total_agree / total_n, 3),
        "agreement_by_criterion": {c: round(v["agree"] / v["n"], 3) for c, v in per_c.items()},
        "product_verdict_agreement_bar5": sum(i["human_pass_bar5"] == i["judge_pass_bar5"] for i in items),
        "human_fails_by_run": {
            run: {c: sum(1 for k in key if k["run"] == run and human[k["item"]][c] == "fail") for c in CRITERIA}
            for run in sorted({k["run"] for k in key})
        },
        "items_detail": items,
        "disagreements": {c: v["disagreements"] for c, v in per_c.items() if v["disagreements"]},
    }
    (HS / "agreement.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: out[k] for k in ("agreement_overall", "agreement_by_criterion", "product_verdict_agreement_bar5", "human_fails_by_run")}, indent=1))
    for c, d in out["disagreements"].items():
        for x in d:
            print(f"{c} {x['item']} {x['run']} human={x['human']} judge={x['judge']} :: {x['judge_reason'][:160]}")
    for i in items:
        print(i["item"], i["run"], "human", i["human_pass_bar5"], "judge", i["judge_pass_bar5"])


if __name__ == "__main__":
    main()
