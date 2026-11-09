"""The four agents: Research, Vision, Draft, Validator.

Each agent is one function with one job. Each loads only the skills it needs
(see skills.py). All facts flow forward as data, so the Validator can check
every claim against the same sources the Draft agent used.
"""
import json
import pathlib

from storefront_agents import checks, llm, skills
from storefront_agents.catalog import BRAND_PATTERN

RESEARCH_CACHE = pathlib.Path("data/research")  # v1 cache; run scripts can point this at another folder
TAGS = ("[THIS PRODUCT]", "[GENERAL]")


def _product_view(p):
    return json.dumps({k: p[k] for k in ("name", "group", "bullets", "description")}, indent=2, ensure_ascii=False)


# --------------------------------------------------------------------------- Research
RESEARCH_PROMPT = """You research facts for a product page in a small coffee, tea and matcha shop.

Product (as sold): {name}
Category: {group}
Search hint (the maker's own product name; use it only to find specs, never repeat the brand): {search_name}
What the catalog already says:
{bullets}

Use Google Search. Find 3-6 short, useful facts a customer would want, such as:
- how to brew or use it at home (water temperature, ratio, time, grind, whisking) for this kind of product
- what the product type is and how it differs from close types (e.g. culinary vs ceremonial matcha)
- for equipment with little catalog data: capacity, power, features of this exact model

Rules:
- Use at most 3 searches.
- Specs of an exact model (capacity, wattage, features) only if the source clearly names this exact model. Otherwise give general facts about this kind of product.
- One fact per line, starting with "- " and then exactly one tag:
  - "[THIS PRODUCT]" only if a page you found names this exact product (same maker and product name, or same model number) and states this fact about it.
  - "[GENERAL]" for everything else: facts about the product type, region, process, style or typical flavor, and brewing advice for this kind of product.
  - If you are not sure, use "[GENERAL]".
- Write a [GENERAL] fact as a general statement ("Sumatran coffees are often wet-hulled"), never as a fact about this bag.
- Facts must be general or about this exact product. Never name a brand or a store.
- No health claims.
- If you cannot find a fact with confidence, leave it out.
"""


def research(p, search_name):
    """Grounded research notes for one product, cached to data/research/<id>.json."""
    cache = RESEARCH_CACHE / f"{p['id']}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    prompt = RESEARCH_PROMPT.format(
        name=p["name"], group=p["group"], search_name=search_name,
        bullets="\n".join(f"- {b}" for b in p["bullets"]) or "(nothing)",
    )
    text, resp = llm.generate("research", [prompt], json_mode=False, tools=llm.search_tool())
    gm = resp.candidates[0].grounding_metadata
    sources = []
    for ch in (gm.grounding_chunks or []) if gm else []:
        if ch.web:
            sources.append({"title": ch.web.title, "uri": ch.web.uri})
    supports = []  # which cited pages back which text, for spot-checks by hand
    for sp in (gm.grounding_supports or []) if gm else []:
        if sp.segment and sp.segment.text:
            supports.append((sp.segment.text.strip(), list(sp.grounding_chunk_indices or [])))
    notes, note_sources, untagged = [], [], 0
    for line in (text or "").splitlines():
        line = line.strip()
        if line.startswith("- "):
            fact = line[2:].replace("**", "").strip()
            tag = next((t for t in TAGS if fact.upper().startswith(t)), None)
            if tag:
                fact = fact[len(tag):].strip()
            else:
                untagged += 1
                tag = "[GENERAL]"  # no tag = not checked for this product
            if fact and not BRAND_PATTERN.search(fact):  # never let a brand through
                notes.append(f"{tag} {fact}")
                idx = sorted({i for seg, ids in supports if seg and (seg in line or fact in seg) for i in ids})
                note_sources.append(idx)
    result = {
        "id": p["id"],
        "notes": notes,
        "sources": sources,
        "note_sources": note_sources,  # per note: indexes into "sources" (from grounding supports; may be empty)
        "untagged_notes": untagged,
        "search_queries": list(gm.web_search_queries or []) if gm else [],
        # Google requires showing Search Suggestions with grounded results; keep it for the demo.
        "search_entry_point": gm.search_entry_point.rendered_content if gm and gm.search_entry_point else None,
    }
    RESEARCH_CACHE.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return result


# --------------------------------------------------------------------------- Vision
VISION_PROMPT = """You look at one product photo for a small coffee, tea and matcha shop.

{skills}

Catalog record for the product this photo should show:
{product}

Return JSON with these keys:
- "alt_text": alt-text for the photo, following the output-format skill. Never name a brand or read out logo text.
- "label_facts": a list of short facts printed on the package (e.g. "light roast", "12 oz (340 g)", "USDA Organic seal", "tasting notes: fresh herbs, cocoa nibs, grapefruit"). Leave out every brand name, logo and slogan.
- "matches_listing": true if the photo shows the same product as the catalog record; false if the package clearly names a different product, roast or flavor.
- "mismatch_reason": one line if matches_listing is false, else "".
"""


def vision(p, issues=None, previous_alt=None):
    skill_text, _ = skills.for_agent("vision")
    prompt = VISION_PROMPT.format(skills=skill_text, product=_product_view(p))
    if issues:
        prompt += (
            f"\nThis is a REVISION of the alt-text. Previous alt-text: {previous_alt!r}\n"
            "Fix these issues:\n" + "\n".join(f"- {i['detail']}" for i in issues) + "\n"
        )
    out, _ = llm.generate("vision", [llm.image_part(p["image"]), prompt], thinking="low")
    out["label_facts"] = [f for f in out.get("label_facts", []) if not BRAND_PATTERN.search(f)]
    return out


# --------------------------------------------------------------------------- Draft
DRAFT_PROMPT = """You write product content for Half Tempo Café's online store.

{skills}

## Sources (the ONLY allowed facts)

[CATALOG]
{product}

[LABEL] facts printed on the package:
{label_facts}

[RESEARCH] notes from cited web sources (tags: see the policy-rules skill, rule P1):
{research}

[STORE] = the store-facts skill above.

## Task

Write the description, the launch brief and nothing else (the alt-text is written by another agent).
{revision}
Return JSON:
{{
  "description": "...",
  "launch_brief": {{"who_its_for": "...", "hook": "...", "social_post": "..."}},
  "claims": [{{"claim": "a factual claim you made", "source": "CATALOG | LABEL | RESEARCH-THIS-PRODUCT | RESEARCH-GENERAL | STORE"}}]
}}
List every factual claim in "claims" with the source it came from. Never copy the tags into the content.
"""


def draft(p, label_facts, research_notes, issues=None, previous=None):
    skill_text, _ = skills.for_agent("draft")
    revision = ""
    if issues:
        revision = (
            "\nThis is a REVISION. Your previous draft:\n"
            + json.dumps({k: previous[k] for k in ("description", "launch_brief")}, ensure_ascii=False)
            + "\nFix every one of these issues and change nothing else that was fine:\n"
            + "\n".join(f"- [{i['rule']}] {i['piece']}: {i['detail']}" for i in issues)
            + "\n"
        )
    prompt = DRAFT_PROMPT.format(
        skills=skill_text,
        product=_product_view(p),
        label_facts="\n".join(f"- {f}" for f in label_facts) or "(none)",
        research="\n".join(f"- {n}" for n in research_notes) or "(none)",
        revision=revision,
    )
    out, _ = llm.generate("draft", [prompt])
    return out


# --------------------------------------------------------------------------- Validator
VALIDATOR_PROMPT = """You are the Validator for Half Tempo Café. You check a draft before it is published.

{skills}

## Sources (the ONLY allowed facts)

[CATALOG]
{product}

[LABEL]
{label_facts}

[RESEARCH]
{research}

## Draft to check
{draft}

The product photo is attached. Check the alt-text against the photo: visible colors, shapes and packaging are fine. Flag alt-text claims that are not visible, subjective feature claims (e.g. "ergonomic"), and any brand name.

Check ONLY these rules (code already checked brand names, banned words, lengths and size placement):
- P1 Facts: is every factual claim in the description, launch brief and alt-text supported by a source above? Upgrades count as failures (e.g. "medium" when the source says "medium-light"). A fact that comes only from a [GENERAL] research note and is stated as a fact about this product fails P1 (e.g. "these beans were wet-hulled" from "[GENERAL] Sumatran coffees are often wet-hulled"); it must be worded as general ("often", "typically", "Sumatran coffees are ...").
- P3 Health: any health or medical claim?
- P4 Promises: any refund, guarantee, price, shipping or stock promise not in store facts?
- P5 Tips: is the brewing or use tip supported, and not contradicted by research?
- U2 Hook: does the hook name a real class or pairing from store facts or the catalog?

Return JSON: {{"issues": [{{"rule": "P1|P3|P4|P5|U2", "piece": "description|who_its_for|hook|social_post|alt_text", "detail": "quote the problem and say why"}}]}}
Return an empty list if nothing is wrong. Do not report style preferences.
"""


def validate(p, out, label_facts, research_notes):
    """Code checks first, then the model check. Returns a list of issues."""
    issues = checks.run(out, p)
    skill_text, _ = skills.for_agent("validator")
    shown = {k: out[k] for k in ("description", "launch_brief", "alt_text") if k in out}
    prompt = VALIDATOR_PROMPT.format(
        skills=skill_text,
        product=_product_view(p),
        label_facts="\n".join(f"- {f}" for f in label_facts) or "(none)",
        research="\n".join(f"- {n}" for n in research_notes) or "(none)",
        draft=json.dumps(shown, indent=2, ensure_ascii=False),
    )
    model_out, _ = llm.generate("validator", [llm.image_part(p["image"]), prompt])
    for i in model_out.get("issues", []) or []:
        if i.get("rule") and i.get("detail"):
            issues.append({"rule": i["rule"], "piece": i.get("piece", "?"), "detail": i["detail"]})
    return issues


def raw_search_name(raw_record):
    """The maker's English product name, used only as a search hint for Research."""
    for v in raw_record.get("item_name", []) or []:
        if v.get("language_tag", "").startswith("en_"):
            return v["value"]
    return ""

