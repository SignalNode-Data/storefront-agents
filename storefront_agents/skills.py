"""Skill library loader. Each agent loads only the skills whose `used_by` names it."""
import pathlib
import re

SKILLS_DIR = pathlib.Path("skills")


def _parse(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    meta, body = {}, text
    if m:
        body = m.group(2).strip()
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    used_by = [s.strip() for s in meta.get("used_by", "").strip("[]").split(",") if s.strip()]
    return {"name": meta.get("skill", path.stem), "version": meta.get("version", "?"), "used_by": used_by, "body": body}


def all_skills():
    return [_parse(p) for p in sorted(SKILLS_DIR.glob("*.md"))]


def for_agent(agent):
    """Return (prompt text, {skill: version}) for one agent."""
    chosen = [s for s in all_skills() if agent in s["used_by"]]
    text = "\n\n".join(f"<skill name=\"{s['name']}\" version=\"{s['version']}\">\n{s['body']}\n</skill>" for s in chosen)
    return text, {s["name"]: s["version"] for s in chosen}
