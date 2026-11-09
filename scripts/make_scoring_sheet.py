"""Build a BLIND hand-scoring sheet: 10 products, 5 from the baseline and 5 from
the pipeline, shuffled, with no label saying which run each came from.

Usage (from repo root):  .venv/bin/python scripts/make_scoring_sheet.py
Writes evals/hand-scoring/sheet.html (open it in a browser; works offline)
and evals/hand-scoring/key.json (which item came from which run; don't open it
until you have exported your scores).
"""
import html
import json
import pathlib
import random
import sys

sys.path.insert(0, ".")
from storefront_agents.catalog import load_catalog  # noqa: E402

SEED = 20261109
CRITERIA = [
    ("T1", "Every factual claim is in the sources (catalog, label on the photo, research notes, store facts)"),
    ("T2", "No brand names and no house-made claims (anywhere, alt-text included)"),
    ("T3", "No health or medical claims"),
    ("T4", "No promises the store hasn't made"),
    ("V1", "Calm, plain; no hype words (perfect as an adjective, best, amazing, elevate, indulge...); max one '!'"),
    ("V2", "One concrete, correct brewing or use tip, or a pairing"),
    ("V3", "Specific to this product, not generic"),
    ("U1", "First two sentences say what it is and how much"),
    ("U2", "Launch brief complete; hook names a real class or pairing"),
    ("A1", "Alt-text describes what is visible; <= 125 characters; no 'Image of'"),
    ("A2", "Alt-text names no brand and claims nothing unseen"),
]


def load(path):
    return {json.loads(l)["id"]: json.loads(l) for l in open(path, encoding="utf-8")}


def main():
    catalog = {p["id"]: p for p in load_catalog()}
    before, after = load("runs/baseline-v1/outputs.jsonl"), load("runs/pipeline-v1/outputs.jsonl")
    ids = [i for i in catalog if i in before and i in after and after[i].get("status") != "hold_photo_mismatch"]
    rng = random.Random(SEED)
    rng.shuffle(ids)
    picked = ids[:10]
    items = [{"pid": pid, "run": "baseline-v1" if k < 5 else "pipeline-v1"} for k, pid in enumerate(picked)]
    rng.shuffle(items)
    for n, it in enumerate(items, 1):
        it["item"] = f"item-{n:02d}"

    out_dir = pathlib.Path("evals/hand-scoring")
    (out_dir / "img").mkdir(parents=True, exist_ok=True)
    (out_dir / "key.json").write_text(json.dumps(items, indent=2) + "\n")

    cards = []
    for it in items:
        p = catalog[it["pid"]]
        r = (before if it["run"] == "baseline-v1" else after)[it["pid"]]
        o = r["output"]
        lb = o.get("launch_brief", {}) or {}
        research = pathlib.Path("data/research") / f"{p['id']}.json"
        notes = json.loads(research.read_text())["notes"] if research.exists() else []
        img = f"img/{it['item']}.jpg"
        (out_dir / img).write_bytes(pathlib.Path(p["image"]).read_bytes())
        e = html.escape
        rows = "".join(
            f'<tr><td><b>{c}</b></td><td>{e(d)}</td>'
            f'<td><label><input type="radio" name="{it["item"]}-{c}" value="pass"> pass</label></td>'
            f'<td><label><input type="radio" name="{it["item"]}-{c}" value="fail"> fail</label></td>'
            f'<td><input type="text" name="{it["item"]}-{c}-note" placeholder="why (if fail)"></td></tr>'
            for c, d in CRITERIA
        )
        cards.append(f"""
<section class="card" id="{it['item']}">
  <h2>{it['item']} · {e(p['name'])}</h2>
  <div class="grid">
    <div><img src="{img}" alt="product photo"></div>
    <div>
      <h3>Sources</h3>
      <p><b>Catalog bullets:</b></p><ul>{''.join(f'<li>{e(b)}</li>' for b in p['bullets']) or '<li>(none)</li>'}</ul>
      <p><b>Research notes:</b></p><ul>{''.join(f'<li>{e(n)}</li>' for n in notes) or '<li>(none)</li>'}</ul>
      <p class="small">Label text on the photo also counts (except brand names). Store facts: see skills/store-facts.md.</p>
    </div>
  </div>
  <h3>Content to score</h3>
  <p><b>Description:</b> {e(o.get('description', ''))}</p>
  <p><b>Who it's for:</b> {e(lb.get('who_its_for', ''))}<br><b>Hook:</b> {e(lb.get('hook', ''))}<br><b>Social post:</b> {e(lb.get('social_post', ''))}</p>
  <p><b>Alt-text:</b> {e(o.get('alt_text', ''))}</p>
  <table>{rows}</table>
</section>""")

    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Hand scoring</title>
<style>
:root {{ --bg:#f7f4ef; --card:#fff; --ink:#222; --muted:#666; --line:#ddd; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#1c1b1a; --card:#262422; --ink:#eee; --muted:#aaa; --line:#444; }} }}
body {{ background:var(--bg); color:var(--ink); font:15px/1.5 system-ui, sans-serif; margin:0; padding:16px; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:16px; margin:0 auto 18px; max-width:980px; }}
.grid {{ display:grid; grid-template-columns: 260px 1fr; gap:16px; }} @media (max-width:760px) {{ .grid {{ grid-template-columns:1fr; }} }}
img {{ width:100%; max-height:320px; object-fit:contain; background:#fff; border-radius:8px; }}
table {{ width:100%; border-collapse:collapse; }} td {{ border-top:1px solid var(--line); padding:6px 4px; vertical-align:top; }}
td input[type=text] {{ width:100%; }} .small {{ color:var(--muted); font-size:13px; }}
.bar {{ position:sticky; top:0; background:var(--bg); padding:8px 0; max-width:980px; margin:0 auto 12px; display:flex; gap:12px; align-items:center; }}
button {{ font:15px system-ui; padding:8px 14px; border-radius:8px; }}
</style></head><body>
<div class="bar"><b>Blind hand scoring</b> · 10 items · <span id="count" class="small"></span>
<button onclick="exportCsv()">Export CSV</button></div>
<div class="card small">Score each criterion pass or fail using rubric v1.x (evals/rubric.md). You don't know which run each item came from, on purpose.
Your answers are saved in this browser as you go. When done, click <b>Export CSV</b> and save the file as <code>evals/hand-scoring/scores.csv</code>.</div>
{''.join(cards)}
<script>
const KEY = "hand-scoring-v1";
const inputs = () => [...document.querySelectorAll("input")];
function save() {{ try {{ const s = {{}}; inputs().forEach(i => {{ if (i.type === "radio") {{ if (i.checked) s[i.name] = i.value; }} else s[i.name] = i.value; }}); localStorage.setItem(KEY, JSON.stringify(s)); }} catch (e) {{}} count(); }}
function load() {{ try {{ const s = JSON.parse(localStorage.getItem(KEY) || "{{}}"); inputs().forEach(i => {{ if (i.type === "radio") i.checked = s[i.name] === i.value; else if (s[i.name]) i.value = s[i.name]; }}); }} catch (e) {{}} count(); }}
function count() {{ const done = new Set(inputs().filter(i => i.type === "radio" && i.checked).map(i => i.name)).size; document.getElementById("count").textContent = done + " / 110 scored"; }}
function exportCsv() {{
  const crit = {json.dumps([c for c, _ in CRITERIA])};
  const items = [...document.querySelectorAll("section.card")].map(s => s.id);
  let csv = "item," + crit.join(",") + ",notes\\n";
  for (const it of items) {{
    const vals = crit.map(c => (document.querySelector(`input[name="${{it}}-${{c}}"]:checked`) || {{}}).value || "");
    const notes = crit.map(c => {{ const v = document.querySelector(`input[name="${{it}}-${{c}}-note"]`).value; return v ? c + ": " + v : ""; }}).filter(Boolean).join(" | ").replaceAll('"', "'");
    csv += it + "," + vals.join(",") + ',"' + notes + '"\\n';
  }}
  const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([csv], {{ type: "text/csv" }})); a.download = "scores.csv"; a.click();
}}
document.addEventListener("change", save); document.addEventListener("input", save); load();
</script></body></html>"""
    (out_dir / "sheet.html").write_text(page, encoding="utf-8")
    print("wrote", out_dir / "sheet.html", "with", len(items), "items")


if __name__ == "__main__":
    main()
