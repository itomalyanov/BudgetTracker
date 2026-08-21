from __future__ import annotations

import duckdb

from budget_tracker.categories import CategoryTaxonomy

# Keyword -> taxonomy leaf category. Matched against "<merchant> <description>"
# (uppercased); first match wins. Best-effort only: many real-world merchants
# (e.g. Temu, IKEA, Econt, Tehnopolis, Tavex) have no equivalent in the default
# taxonomy and are intentionally left uncategorized rather than guessed — extend
# this list, or add categories to categories.json, as more merchants are seen.
MERCHANT_KEYWORD_RULES: list[tuple[str, str]] = [
    ("LIDL", "Groceries"),
    ("KAUFLAND", "Groceries"),
    ("BILLA", "Groceries"),
    ("FANTASTICO", "Groceries"),
    ("T MARKET", "Groceries"),
    ("GLOVO", "Restaurant"),
    ("MCDONALDS", "Restaurant"),
    ("KFC", "Restaurant"),
    ("EKO BLAGOEVGRAD", "Fuel"),
    ("EKO ", "Fuel"),
    ("SHELL", "Fuel"),
    ("OMV", "Fuel"),
    ("PETROL", "Fuel"),
    ("LUKOIL", "Fuel"),
    ("VIVACOM", "Phone"),
    ("YETTEL", "Phone"),
    ("ЧЕЗ", "Electricity"),
    ("CEZ ELEKTRO", "Electricity"),
    ("ЕВН", "Electricity"),
    ("EVN BULGARIA", "Electricity"),
    ("SOPHARMACY", "Pharmacy"),
    ("АПТЕКА", "Pharmacy"),
]


def categorize_merchant(
    merchant: str | None,
    description: str,
    taxonomy: CategoryTaxonomy,
    rules: list[tuple[str, str]] = MERCHANT_KEYWORD_RULES,
) -> tuple[str | None, str | None]:
    """Best-effort (leaf_category, category_group) for a transaction, or (None, None)."""
    haystack = f"{merchant or ''} {description}".upper()
    for keyword, leaf in rules:
        if keyword in haystack and taxonomy.is_known_category(leaf):
            return leaf, taxonomy.group_for_leaf(leaf)
    return None, None


def apply_categories(
    conn: duckdb.DuckDBPyConnection,
    taxonomy: CategoryTaxonomy,
    rules: list[tuple[str, str]] = MERCHANT_KEYWORD_RULES,
) -> int:
    """Assigns category/category_group to every currently-uncategorized transaction.

    Safe to re-run at any time (e.g. after extending the rule set) — only rows
    with category IS NULL are touched. Returns the number of rows updated.
    """
    rows = conn.execute(
        "SELECT id, merchant, description FROM transactions WHERE category IS NULL"
    ).fetchall()
    updated = 0
    for txn_id, merchant, description in rows:
        leaf, group = categorize_merchant(merchant, description, taxonomy, rules)
        if leaf is None:
            continue
        conn.execute(
            "UPDATE transactions SET category = ?, category_group = ? WHERE id = ?",
            [leaf, group, txn_id],
        )
        updated += 1
    return updated
