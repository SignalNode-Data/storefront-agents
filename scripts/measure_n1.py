"""N1 measure: research-only facts stated as facts about this product.

Usage (from repo root):
    .venv/bin/python scripts/measure_n1.py RUN_NAME --research DIR

Same method for every run. One model call per product. The model sees the
catalog record, the label facts, the research notes WITHOUT tags, and the
content. It lists each origin, process, flavor or spec claim that appears only
in the research notes (not in the catalog or on the label), says which note it
came from, and says how it is worded:
  "product": stated as a fact about this product ("these beans were wet-hulled")
  "general": stated as true of the type ("Sumatran coffees are often wet-hulled")
Brewing and use tips are left out (they are advice for the type, not product facts).

Code then looks up each note's tag in the research cache (v2 caches have tags;
v1 caches have none). N1 = a "product"-worded claim whose note is not tagged
[THIS PRODUCT]. This is Claude's check, not the blind hand-scoring.

Writes runs/RUN_NAME/n1.jsonl and runs/RUN_NAME/n1.json
"""
import json
import pathlib
import re
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, ".")
from storefront_agents import llm  # noqa: E402
from storefront_agents.catalog import load_catalog  # noqa: E402

TAG = re.compile(r"^\[(THIS PRODUCT|GENERAL)\]\s*")

PROMPT = """You audit product content for a small coffee, tea and matcha shop.

[CATALOG]
{catalog}

[LABEL] facts printed on the package:
{label}

[RESEARCH] numbered notes from web pages:
{research}

[CONTENT]
{content}

List every claim in CONTENT about origin (country, region, altitude, farm, cooperative),
process (washed, natural, wet-hulled, shade-grown, roasting method), variety or grade,
flavor, aroma or texture, or equipment specs (capacity, power, materials, features)
that is supported ONLY by a RESEARCH note: it is not in CATALOG and not in LABEL.
Leave out brewing and use tips (temperature, ratio, time, grind, whisking).

For each claim give:
- "quote": the exact words from CONTENT
- "note": the number of the RESEARCH note it comes from
- "kind": "origin" | "process" | "flavor" | "spec" | "other"
- "worded_as": "product" if CONTENT states it as a fact about this product
  ("these beans were wet-hulled", "grown at 1,400 m", "notes of honey");
  "general" if CONTENT states it as true of the type or region
  ("Sumatran coffees are often wet-hulled", "matcha is typically shade-grown").

Return JSON: {{"claims": [{{"quote": "...", "note": 1, "kind": "...", "worded_as": "..."}}]}}
Return an empty list if there are none.
"""


def main():
    args = sys.argv[1:]
    research_dir = pathlib.Path(args[args.index("--research") + 1]) if "--research" in args else pathlib.Path("data/research")
    run_name = args[0]
    run_dir = pathlib.Path("runs") / run_name
    catalog = {p["id"]: p for p in load_catalog()}
    rows = [json.loads(line) for line in open(run_dir / "outputs.jsonl", encoding="utf-8")]

    def one(r):
        p = catalog[r["id"]]
        cache = json.loads((research_dir / f"{r['id']}.json").read_text())
        notes = cache["notes"]
        tags = [(TAG.match(n).group(1) if TAG.match(n) else None) for n in notes]
        plain = [TAG.sub("", n) for n in notes]
        content = {k: r["output"].get(k) for k in ("description", "launch_brief")}
        prompt = PROMPT.format(
            catalog=json.dumps({k: p[k] for k in ("name", "group", "bullets", "description")}, indent=2, ensure_ascii=False),
            label="\n".join(f"- {f}" for f in r.get("label_facts", [])) or "(none)",
            research="\n".join(f"{i + 1}. {n}" for i, n in enumerate(plain)) or "(none)",
            content=json.dumps(content, indent=2, ensure_ascii=False),
        )
        try:
            out, _ = llm.generate("n1", [prompt])
        except Exception as e:
            return {"id": r["id"], "error": str(e)[:300]}
        claims = []
        for c in out.get("claims", []) or []:
            n = c.get("note")
            i = n - 1 if isinstance(n, int) and 0 < n <= len(notes) else None
            tag = tags[i] if i is not None else None
            c["note_text"] = plain[i] if i is not None else None
            c["note_tag"] = tag
            c["n1"] = c.get("worded_as") == "product" and tag != "THIS PRODUCT"
            claims.append(c)
        return {"id": r["id"], "name": r["name"], "group": r["group"], "claims": claims}

    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(one, rows))
    with open(run_dir / "n1.jsonl", "w", encoding="utf-8") as f:
        for x in results:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    ok = [x for x in results if "claims" in x]
    allc = [c for x in ok for c in x["claims"]]
    summary = {
        "run": run_name,
        "research_dir": str(research_dir),
        "products": len(ok),
        "errors": len(results) - len(ok),
        "research_only_claims": len(allc),
        "worded_as_product": sum(c.get("worded_as") == "product" for c in allc),
        "worded_as_general": sum(c.get("worded_as") == "general" for c in allc),
        "product_worded_from_this_product_note": sum(c.get("worded_as") == "product" and c["note_tag"] == "THIS PRODUCT" for c in allc),
        "n1_claims": sum(c["n1"] for c in allc),
        "n1_products": sum(any(c["n1"] for c in x["claims"]) for x in ok),
        "usage": llm.USAGE.get("n1"),
    }
    (run_dir / "n1.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
