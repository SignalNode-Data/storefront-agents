"""Catalog loader: turns the raw ABO records into the Half Tempo Café catalog.

YOUR EXERCISE (Block 3 practice). Write `load_catalog`. Run the tests with:

    .venv/bin/pytest tests/test_catalog.py -v

Done = every test passes.

Inputs
------
- data/abo/selected_listings.jsonl : one raw ABO record per line (JSON).
  Useful fields: "item_id", "bullet_point", "product_description".
  Text fields are lists of {"language_tag": "en_US", "value": "..."}.
  Keep only entries whose language_tag starts with "en_".
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

Hints: json.loads, csv.DictReader, a dict keyed by item_id, BRAND_PATTERN.search(text).
"""
import re

BRAND_PATTERN = re.compile(
    r"amazon|allegro|wickedly prime|vedaka|whole foods|365 every|365 by|solimo|happy belly|fresh brand",
    re.IGNORECASE,
)


def load_catalog(
    listings_path="data/abo/selected_listings.jsonl",
    selection_path="data/selection.csv",
    images_dir="data/abo/images",
):
    """Return the catalog as a list of dicts. See the module docstring."""
    raise NotImplementedError("Write me!")
