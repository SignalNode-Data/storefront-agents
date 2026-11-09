"""Catalog loader: turns the raw ABO records into the Half Tempo Café catalog.

Run the tests from the repo root with:

    .venv/bin/pytest tests/test_catalog.py -v

Inputs
------
- data/abo/selected_listings.jsonl : one raw ABO record per line (JSON).
  Useful fields: "item_id", "bullet_point", "product_description".
  Text fields are lists of {"language_tag": "en_US", "value": "..."}.
- data/selection.csv : item_id, group, display_name (one row per product).
- data/abo/images/<item_id>.jpg : the product photo.

Output
------
A list of dicts, in the same order as selection.csv, each shaped like:

    {
        "id": "B06XS91CKW",
        "group": "matcha",
        "name": "Organic Matcha Green Tea Powder, Culinary Grade, 4 oz",
        "bullets": ["One 4-ounce resealable bag", "Culinary grade powder", ...],
        "description": "",          # English product_description, or "" if none
        "image": "data/abo/images/B06XS91CKW.jpg",
    }

Rules
-----
1. "name" comes from selection.csv (display_name), not from the raw record.
2. "bullets": English only, stripped of spaces at both ends, no empty strings,
   no duplicates (keep the first time a bullet appears).
3. Drop any bullet that matches BRAND_PATTERN (for example "An Amazon brand").
   Apply the same check to "description": if it matches, use "" instead.
4. Some products have no bullets at all. That is fine: return [].
"""
import csv
import json
import re

BRAND_PATTERN = re.compile(
    r"amazon|allegro|wickedly prime|vedaka|whole foods|365 every|365 by|solimo|happy belly|fresh brand",
    re.IGNORECASE,
)


def english(values):
    """Return the English texts from an ABO text field, stripped.

    An ABO text field looks like:
        [{"language_tag": "en_US", "value": "..."}, {"language_tag": "de_DE", ...}]
    The field can also be missing (None). Then this returns [].
    """
    texts = []
    for entry in values or []:
        if entry.get("language_tag", "").startswith("en_"):
            texts.append(entry.get("value", "").strip())
    return texts


def clean_bullets(record):
    """English bullets with empties, duplicates and brand mentions removed."""
    bullets = []
    for bullet in english(record.get("bullet_point")):
        if not bullet:
            continue  # empty after stripping
        if bullet in bullets:
            continue  # same bullet already kept (ABO repeats en_US and en_GB copies)
        if BRAND_PATTERN.search(bullet):
            continue  # names a brand, e.g. "An Amazon brand"
        bullets.append(bullet)
    return bullets


def clean_description(record):
    """First English product description, or "" if none or if it names a brand."""
    descriptions = english(record.get("product_description"))
    if not descriptions:
        return ""
    description = descriptions[0]
    if BRAND_PATTERN.search(description):
        return ""
    return description


def load_catalog(
    listings_path="data/abo/selected_listings.jsonl",
    selection_path="data/selection.csv",
    images_dir="data/abo/images",
):
    """Return the catalog as a list of dicts. See the module docstring."""
    # 1. Read every raw record into a dict keyed by item_id, for fast lookup.
    raw = {}
    with open(listings_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                raw[record["item_id"]] = record

    # 2. Walk selection.csv in order and build one clean product per row.
    catalog = []
    with open(selection_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            item_id = row["item_id"]
            record = raw[item_id]  # KeyError here = selection.csv names an ID we don't have
            catalog.append(
                {
                    "id": item_id,
                    "group": row["group"],
                    "name": row["display_name"],
                    "bullets": clean_bullets(record),
                    "description": clean_description(record),
                    "image": f"{images_dir}/{item_id}.jpg",
                }
            )
    return catalog
