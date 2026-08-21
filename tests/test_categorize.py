from __future__ import annotations

from datetime import date
from decimal import Decimal

from budget_tracker import db
from budget_tracker.categorize import apply_categories, categorize_merchant
from budget_tracker.models import Transaction, TransactionType


def test_categorize_merchant_matches_known_keyword(taxonomy):
    leaf, group = categorize_merchant("BGR BLAGOEVGRAD LIDL BALGARIYA EOOD", "", taxonomy)
    assert leaf == "Groceries"
    assert group == "food"


def test_categorize_merchant_unmatched_returns_none(taxonomy):
    leaf, group = categorize_merchant("SOME UNKNOWN SHOP", "", taxonomy)
    assert leaf is None
    assert group is None


def test_categorize_merchant_ignores_rule_for_unknown_taxonomy_leaf(taxonomy):
    leaf, _ = categorize_merchant("TEST", "TEST", taxonomy, rules=[("TEST", "NotARealCategory")])
    assert leaf is None


def test_apply_categories_updates_matching_rows_only(db_conn, taxonomy):
    txns = [
        Transaction(
            date=date(2024, 1, 5),
            amount=Decimal("-20.00"),
            description="524710xxxxxx5728 POS",
            transaction_type=TransactionType.CARD_PHYSICAL,
            merchant="BGR BLAGOEVGRAD LIDL BALGARIYA EOOD",
            external_id="c1",
        ),
        Transaction(
            date=date(2024, 1, 6),
            amount=Decimal("-15.00"),
            description="524710xxxxxx5728 POS",
            transaction_type=TransactionType.CARD_PHYSICAL,
            merchant="UNKNOWN RETAIL SHOP",
            external_id="c2",
        ),
    ]
    db.insert_transactions(db_conn, txns)

    updated = apply_categories(db_conn, taxonomy)
    assert updated == 1

    rows = db_conn.execute(
        "SELECT merchant, category, category_group FROM transactions ORDER BY merchant"
    ).fetchall()
    by_merchant = {r[0]: (r[1], r[2]) for r in rows}
    assert by_merchant["BGR BLAGOEVGRAD LIDL BALGARIYA EOOD"] == ("Groceries", "food")
    assert by_merchant["UNKNOWN RETAIL SHOP"] == (None, None)


def test_apply_categories_is_idempotent_and_skips_already_categorized(db_conn, taxonomy):
    txn = Transaction(
        date=date(2024, 1, 5),
        amount=Decimal("-20.00"),
        description="POS",
        transaction_type=TransactionType.CARD_PHYSICAL,
        merchant="LIDL",
        external_id="c3",
    )
    db.insert_transactions(db_conn, [txn])
    first = apply_categories(db_conn, taxonomy)
    second = apply_categories(db_conn, taxonomy)
    assert first == 1
    assert second == 0
