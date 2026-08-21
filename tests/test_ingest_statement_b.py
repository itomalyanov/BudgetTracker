from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from budget_tracker.ingest.statement_b import parse_statement_b
from budget_tracker.models import TransactionType

SAMPLE = Path(__file__).parent / "fixtures" / "statement_b_sample.html"


def test_parses_expected_transaction_count():
    txns = parse_statement_b(SAMPLE)
    assert len(txns) == 5


def test_merchant_is_always_none_for_shape_b():
    txns = parse_statement_b(SAMPLE)
    assert all(t.merchant is None for t in txns)


def test_amounts_and_dates_parsed_correctly():
    txns = parse_statement_b(SAMPLE)
    txns_by_auth = {t.auth_code: t for t in txns}
    assert txns_by_auth["EEE555"].amount == Decimal("-8.22")
    assert txns_by_auth["EEE555"].date == date(2024, 3, 14)
    assert txns_by_auth["FFF666"].amount == Decimal("-18.00")


def test_amount_converted_to_eur_on_or_after_adoption_date():
    txns = parse_statement_b(SAMPLE)
    txns_by_auth = {t.auth_code: t for t in txns}
    converted = txns_by_auth["GGG777"]
    assert converted.currency == "EUR"
    assert converted.amount == Decimal("-10.00")
    assert txns_by_auth["EEE555"].currency == "BGN"


def test_classified_as_card_physical():
    txns = parse_statement_b(SAMPLE)
    assert all(t.transaction_type == TransactionType.CARD_PHYSICAL for t in txns)


def test_footer_total_row_is_skipped():
    txns = parse_statement_b(SAMPLE)
    assert len(txns) == 5  # not 6 — the "Общо" row must not be parsed as a transaction


def test_duplicate_looking_rows_get_distinct_external_ids():
    txns = parse_statement_b(SAMPLE)
    matching = [t for t in txns if t.auth_code == "HHH888"]
    assert len(matching) == 2
    assert matching[0].external_id != matching[1].external_id


def test_duplicate_looking_rows_both_survive_insert(db_conn):
    from budget_tracker import db

    txns = parse_statement_b(SAMPLE)
    db.insert_transactions(db_conn, txns)
    count = db_conn.execute(
        "SELECT count(*) FROM transactions WHERE auth_code = 'HHH888'"
    ).fetchone()[0]
    assert count == 2
