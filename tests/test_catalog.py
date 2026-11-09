"""Tests for the catalog loader. Run from the repo root: .venv/bin/pytest -v"""
import csv
import os
from collections import Counter

import pytest

from storefront_agents.catalog import BRAND_PATTERN, load_catalog

THIN_DATA_ITEM = "B087X76Z3W"  # gooseneck kettle: no bullets in ABO, kept on purpose


@pytest.fixture(scope="module")
def catalog():
    return load_catalog()


@pytest.fixture(scope="module")
def selection():
    with open("data/selection.csv", newline="") as f:
        return list(csv.DictReader(f))


def test_one_product_per_selection_row_in_order(catalog, selection):
    assert [p["id"] for p in catalog] == [row["item_id"] for row in selection]


def test_every_product_has_the_right_keys(catalog):
    for p in catalog:
        assert set(p) == {"id", "group", "name", "bullets", "description", "image"}, p["id"]


def test_names_and_groups_come_from_selection(catalog, selection):
    for p, row in zip(catalog, selection):
        assert p["name"] == row["display_name"]
        assert p["group"] == row["group"]


def test_group_counts(catalog):
    assert Counter(p["group"] for p in catalog) == {
        "matcha": 5, "tea": 9, "coffee": 8, "gear": 3, "pairing": 7,
    }


def test_every_image_exists(catalog):
    for p in catalog:
        assert p["image"] == f"data/abo/images/{p['id']}.jpg"
        assert os.path.isfile(p["image"]), p["image"]


def test_no_brand_names_anywhere(catalog):
    for p in catalog:
        for text in [p["name"], p["description"], *p["bullets"]]:
            assert not BRAND_PATTERN.search(text), (p["id"], text)


def test_bullets_are_clean(catalog):
    for p in catalog:
        assert len(p["bullets"]) == len(set(p["bullets"])), f"duplicates in {p['id']}"
        for b in p["bullets"]:
            assert b and b == b.strip(), (p["id"], repr(b))


def test_bullets_present_except_thin_data_item(catalog):
    for p in catalog:
        if p["id"] == THIN_DATA_ITEM:
            assert p["bullets"] == []
        else:
            assert len(p["bullets"]) >= 1, f"{p['id']} lost all its bullets"
