"""Code checks the Validator runs before asking the model. Cheap, exact, repeatable."""
import re

from storefront_agents.catalog import BRAND_PATTERN

HYPE = re.compile(
    r"\b(best|amazing|ultimate|life-changing|game-?changer|must-have|elevat\w*|unleash\w*|indulg\w*|revolutionary)\b"
    r"|\bperfect(?=\s+(?:\w+\s+)?(?:cup|companion|match|pairing|balance|brew|way|choice|treat|start|pick|gift|blend|partner|addition|foam))"
    r"|\bperfect\b(?!ing|ly)(?=[\s.,!])(?<!\bperfecting)",
    re.I,
)
SIZE = re.compile(r"\b\d+(?:\.\d+)?[\s-]*(?:oz|ounce|ounces|g|gram|grams|kg|ml|l|liter|litre|count|ct|sachets|bags?)\b|\bfour-ounce|\beight-ounce|\bone-ounce", re.I)
EMOJI = re.compile(r"[\U0001F300-\U0001FAFF☀-➿]")


def pieces(out):
    lb = out.get("launch_brief", {}) or {}
    return {
        "description": out.get("description", "") or "",
        "who_its_for": lb.get("who_its_for", "") or "",
        "hook": lb.get("hook", "") or "",
        "social_post": lb.get("social_post", "") or "",
        "alt_text": out.get("alt_text", "") or "",
    }


def first_sentences(text, n=2):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(parts[:n])


def run(out, product):
    """Return a list of issues: {"rule", "piece", "detail"}."""
    issues = []
    p = pieces(out)
    for name, text in p.items():
        for m in BRAND_PATTERN.finditer(text):
            issues.append({"rule": "P2 brand", "piece": name, "detail": f"brand name '{m.group(0)}'"})
        for m in HYPE.finditer(text):
            issues.append({"rule": "V1 hype", "piece": name, "detail": f"hype word '{m.group(0)}'"})
    if sum(t.count("!") for t in p.values()) > 1:
        issues.append({"rule": "V1 hype", "piece": "all", "detail": "more than one exclamation mark"})
    if EMOJI.search(p["description"]):
        issues.append({"rule": "V1 hype", "piece": "description", "detail": "emoji in description"})
    words = len(p["description"].split())
    if not 80 <= words <= 150:
        issues.append({"rule": "format", "piece": "description", "detail": f"{words} words (need 80-150)"})
    if len(p["alt_text"]) > 125:
        issues.append({"rule": "format", "piece": "alt_text", "detail": f"{len(p['alt_text'])} characters (max 125)"})
    if re.match(r"^\s*(image|picture|photo) of", p["alt_text"], re.I):
        issues.append({"rule": "format", "piece": "alt_text", "detail": "starts with 'Image of'"})
    if len(p["social_post"]) > 200:
        issues.append({"rule": "format", "piece": "social_post", "detail": f"{len(p['social_post'])} characters (max 200)"})
    if SIZE.search(product["name"]) and not SIZE.search(first_sentences(p["description"])):
        issues.append({"rule": "U1 size", "piece": "description", "detail": "size or quantity not in the first two sentences"})
    return issues
