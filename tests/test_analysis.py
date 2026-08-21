from __future__ import annotations

from datetime import date
from decimal import Decimal

from budget_tracker import analysis, db
from budget_tracker.models import Transaction, TransactionType


def _seed(conn):
    txns = [
        Transaction(
            date=date(2024, 1, 5),
            amount=Decimal("-20.00"),
            description="Groceries",
            transaction_type=TransactionType.CARD_PHYSICAL,
            merchant="Kaufland",
            category="Groceries",
            category_group="food",
            external_id="t1",
        ),
        Transaction(
            date=date(2024, 1, 6),
            amount=Decimal("-30.00"),
            description="Groceries",
            transaction_type=TransactionType.CARD_PHYSICAL,
            merchant="Kaufland",
            category="Groceries",
            category_group="food",
            external_id="t2",
        ),
        Transaction(
            date=date(2024, 1, 6),
            amount=Decimal("-100.00"),
            description="ATM",
            transaction_type=TransactionType.ATM_WITHDRAWAL,
            external_id="t3",
        ),
        Transaction(
            date=date(2024, 1, 7),
            amount=Decimal("1500.00"),
            description="Salary",
            transaction_type=TransactionType.INCOMING_TRANSFER,
            external_id="t4",
        ),
        Transaction(
            date=date(2024, 1, 7),
            amount=Decimal("-9.99"),
            description="Pending hold",
            transaction_type=TransactionType.CARD_PHYSICAL,
            is_settled=False,
            external_id="t5",
        ),
    ]
    db.insert_transactions(conn, txns)


def test_spend_by_date_range_excludes_income_by_default(db_conn):
    _seed(db_conn)
    rows = analysis.spend_by_date_range(db_conn, date(2024, 1, 1), date(2024, 1, 31)).fetchall()
    totals = dict(rows)
    assert totals[date(2024, 1, 5)] == Decimal("-20.00")
    assert totals[date(2024, 1, 6)] == Decimal("-130.00")
    assert date(2024, 1, 7) not in totals or totals[date(2024, 1, 7)] == Decimal("0.00")


def test_spend_by_date_range_can_include_income(db_conn):
    _seed(db_conn)
    rows = analysis.spend_by_date_range(
        db_conn, date(2024, 1, 1), date(2024, 1, 31), include_income=True
    ).fetchall()
    totals = dict(rows)
    assert totals[date(2024, 1, 7)] == Decimal("1500.00")


def test_spend_by_date_range_excludes_unsettled_holds(db_conn):
    _seed(db_conn)
    rows = analysis.spend_by_date_range(
        db_conn, date(2024, 1, 1), date(2024, 1, 31), include_income=True
    ).fetchall()
    totals = dict(rows)
    assert totals[date(2024, 1, 7)] == Decimal("1500.00")  # the -9.99 hold is excluded


def test_spend_by_merchant(db_conn):
    _seed(db_conn)
    rows = analysis.spend_by_merchant(db_conn).fetchall()
    by_merchant = {r[0]: r[1] for r in rows}
    assert by_merchant["Kaufland"] == Decimal("50.00")


def test_spend_by_amount_filters_range(db_conn):
    _seed(db_conn)
    rows = analysis.spend_by_amount(db_conn, min_amount=25, max_amount=200).fetchall()
    spent_values = {r[4] for r in rows}
    assert Decimal("30.00") in spent_values
    assert Decimal("100.00") in spent_values
    assert Decimal("20.00") not in spent_values


def test_category_rollup_by_group(db_conn):
    _seed(db_conn)
    rows = analysis.category_rollup(db_conn, group_by="group").fetchall()
    by_group = {r[0]: r[1] for r in rows}
    assert by_group["food"] == Decimal("50.00")
