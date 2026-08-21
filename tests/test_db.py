from __future__ import annotations

from datetime import date
from decimal import Decimal

from budget_tracker import db
from budget_tracker.models import Transaction, TransactionType


def test_ensure_schema_is_idempotent(db_conn):
    db.ensure_schema(db_conn)
    db.ensure_schema(db_conn)
    versions = db_conn.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall()
    assert versions == [(1,), (2,), (3,)]


def test_insert_and_query_round_trip(db_conn):
    txn = Transaction(
        date=date(2024, 12, 11),
        amount=Decimal("-48.50"),
        description="524710xxxxxx5728 PLASHTANE NA POS",
        transaction_type=TransactionType.CARD_PHYSICAL,
        merchant="DIVELI EOOD",
        external_id="ext-1",
    )
    db.insert_transaction(db_conn, txn)
    rows = db_conn.execute("SELECT merchant, amount, transaction_type FROM transactions").fetchall()
    assert rows == [("DIVELI EOOD", Decimal("-48.50"), "card_physical")]


def test_external_id_uniqueness_prevents_duplicate_import(db_conn):
    txn = Transaction(
        date=date(2024, 12, 11),
        amount=Decimal("-9.46"),
        description="POS",
        transaction_type=TransactionType.CARD_PHYSICAL,
        external_id="dup-id",
    )
    db.insert_transactions(db_conn, [txn, txn])
    count = db_conn.execute("SELECT count(*) FROM transactions").fetchone()[0]
    assert count == 1


def test_insert_transactions_without_external_id_never_conflict(db_conn):
    txns = [
        Transaction(
            date=date(2024, 12, 11),
            amount=Decimal("-5.00"),
            description="POS",
            transaction_type=TransactionType.CARD_PHYSICAL,
        )
        for _ in range(3)
    ]
    db.insert_transactions(db_conn, txns)
    count = db_conn.execute("SELECT count(*) FROM transactions").fetchone()[0]
    assert count == 3


def test_transactions_display_view_formats_date_as_plain_string(db_conn):
    txn = Transaction(
        date=date(2026, 3, 12),
        amount=Decimal("-25.49"),
        description="POS",
        transaction_type=TransactionType.CARD_PHYSICAL,
        external_id="disp-1",
    )
    db.insert_transaction(db_conn, txn)
    row = db_conn.execute(
        "SELECT date FROM transactions_display WHERE external_id = 'disp-1'"
    ).fetchone()
    assert row == ("2026-03-12",)


def test_load_categories(db_conn):
    db.load_categories(db_conn, [("food", None, "Groceries"), ("transportation", "car", "Fuel")])
    rows = db_conn.execute(
        "SELECT top_group, subgroup, leaf FROM categories ORDER BY leaf"
    ).fetchall()
    assert rows == [("transportation", "car", "Fuel"), ("food", None, "Groceries")]
