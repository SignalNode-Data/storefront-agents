"""The pipeline: Research + Vision -> Draft -> Validator -> (one revision) -> status.

Status per product:
- "publish": passed the Validator (first try or after one revision)
- "needs_review": still has issues after one revision
- "hold_photo_mismatch": the photo shows a different product (P6); never auto-published
"""
from storefront_agents import agents

MAX_REVISIONS = 1


def run_product(p, raw_record):
    research = agents.research(p, agents.raw_search_name(raw_record))
    seen = agents.vision(p)
    label_facts = seen.get("label_facts", [])
    notes = research["notes"]

    history = []
    out = agents.draft(p, label_facts, notes)
    out["alt_text"] = seen.get("alt_text", "")
    issues = agents.validate(p, out, label_facts, notes)
    history.append({"draft": out, "issues": issues})

    revisions = 0
    while issues and revisions < MAX_REVISIONS:
        revisions += 1
        alt_issues = [i for i in issues if i["piece"] == "alt_text"]
        text_issues = [i for i in issues if i["piece"] != "alt_text"]
        previous_alt = out["alt_text"]
        if text_issues:
            out = agents.draft(p, label_facts, notes, issues=text_issues, previous=out)
        else:
            out = dict(out)  # copy, so the history keeps the earlier round unchanged
        out["alt_text"] = previous_alt
        if alt_issues:  # alt-text belongs to Vision: ask it again, once, with the issues
            seen = agents.vision(p, issues=alt_issues, previous_alt=out["alt_text"])
            out["alt_text"] = seen.get("alt_text", "")
        issues = agents.validate(p, out, label_facts, notes)
        history.append({"draft": out, "issues": issues})

    if seen.get("matches_listing") is False:
        status = "hold_photo_mismatch"
    elif issues:
        status = "needs_review"
    else:
        status = "publish"

    return {
        "id": p["id"],
        "name": p["name"],
        "group": p["group"],
        "status": status,
        "output": {k: out.get(k) for k in ("description", "launch_brief", "alt_text")},
        "claims": out.get("claims", []),
        "label_facts": label_facts,
        "photo_matches_listing": seen.get("matches_listing"),
        "mismatch_reason": seen.get("mismatch_reason", ""),
        "research_notes": notes,
        "research_sources": research["sources"],
        "revisions": revisions,
        "remaining_issues": issues,
        "history": history,
    }
