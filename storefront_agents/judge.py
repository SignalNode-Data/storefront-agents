"""Gemini-as-judge: scores one output against the rubric, criterion by criterion.

The judge is independent of the pipeline: it reads the rubric file as written,
sees the same sources for the before and the after run, and never sees the
Validator's verdict.
"""
import json
import pathlib

from storefront_agents import llm

CRITERIA = ["T1", "T2", "T3", "T4", "V1", "V2", "V3", "U1", "U2", "A1", "A2"]
TRUTH = ["T1", "T2", "T3", "T4"]
QUALITY = ["V1", "V2", "V3", "U1", "U2", "A1", "A2"]

JUDGE_PROMPT = """You are a strict, fair grader. Score one product's content against the rubric below.

<rubric>
{rubric}
</rubric>

<store_facts>
{store_facts}
</store_facts>

<sources>
[CATALOG]
{catalog}

[RESEARCH] (cited web notes; allowed sources)
{research}

[PHOTO] The product photo is attached. {photo_rule}
</sources>

<content_to_score>
{content}
</content_to_score>

For EACH criterion {criteria}, decide pass or fail using only the rubric's wording.
Return JSON: {{"T1": {{"pass": true, "reason": "one line"}}, ...}} with all {n} criteria.
A reason for a fail must quote the problem.
"""


def _strip_front_matter(text):
    return text.split("---", 2)[2].strip() if text.startswith("---") else text


def score(product, output, research_notes, photo_is_source=True):
    rubric = pathlib.Path("evals/rubric.md").read_text(encoding="utf-8")
    facts = _strip_front_matter(pathlib.Path("skills/store-facts.md").read_text(encoding="utf-8"))
    photo_rule = (
        "Text printed on the package (except brand names) counts as an allowed source of facts."
        if photo_is_source
        else "Use the photo only to judge the alt-text; it is not a source of facts."
    )
    content = {k: output.get(k) for k in ("description", "launch_brief", "alt_text")}
    prompt = JUDGE_PROMPT.format(
        rubric=rubric,
        store_facts=facts,
        catalog=json.dumps({k: product[k] for k in ("name", "group", "bullets", "description")}, indent=2, ensure_ascii=False),
        research="\n".join(f"- {n}" for n in research_notes) or "(none)",
        photo_rule=photo_rule,
        content=json.dumps(content, indent=2, ensure_ascii=False),
        criteria=", ".join(CRITERIA),
        n=len(CRITERIA),
    )
    out, _ = llm.generate("judge", [llm.image_part(product["image"]), prompt])
    result = {}
    for c in CRITERIA:
        v = out.get(c, {}) or {}
        result[c] = {"pass": bool(v.get("pass")), "reason": v.get("reason", "")}
    return result


def product_passes(scores, quality_bar=5):
    return all(scores[c]["pass"] for c in TRUTH) and sum(scores[c]["pass"] for c in QUALITY) >= quality_bar
