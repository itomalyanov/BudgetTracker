from __future__ import annotations

from budget_tracker.categories import CategoryTaxonomy


def test_flat_list_shape(taxonomy: CategoryTaxonomy):
    assert taxonomy.group_for_leaf("Groceries") == "food"
    assert taxonomy.group_for_leaf("Restaurant") == "food"


def test_nested_dict_shape(taxonomy: CategoryTaxonomy):
    assert taxonomy.group_for_leaf("Fuel") == "transportation"
    assert taxonomy.group_for_leaf("Dental") == "bills"


def test_scalar_string_shape(taxonomy: CategoryTaxonomy):
    assert taxonomy.group_for_leaf("Hobby Project") == "hobby"


def test_unknown_leaf_returns_none(taxonomy: CategoryTaxonomy):
    assert taxonomy.group_for_leaf("Not A Real Category") is None
    assert taxonomy.is_known_category("Not A Real Category") is False


def test_is_known_category(taxonomy: CategoryTaxonomy):
    assert taxonomy.is_known_category("Groceries") is True


def test_as_rows_matches_leaf_count(taxonomy: CategoryTaxonomy):
    rows = taxonomy.as_rows()
    assert len(rows) == len(taxonomy.leaf_names())
    assert ("food", None, "Groceries") in rows
    assert ("transportation", "car", "Fuel") in rows


def test_deeply_nested_and_mixed_shapes_via_from_json(tmp_path):
    path = tmp_path / "categories.json"
    path.write_text('{"a": ["x", "y"], "b": {"c": {"d": ["z"]}}, "e": "single"}', encoding="utf-8")
    tax = CategoryTaxonomy.from_json(path)
    assert tax.group_for_leaf("x") == "a"
    assert tax.group_for_leaf("z") == "b"
    assert tax.group_for_leaf("single") == "e"
