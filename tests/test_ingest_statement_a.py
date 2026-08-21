from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from budget_tracker.ingest.statement_a import parse_statement_a
from budget_tracker.models import TransactionType

SAMPLE = Path(__file__).parent / "fixtures" / "statement_a_sample.html"


def test_parses_expected_transaction_count():
    txns = parse_statement_a(SAMPLE)
    # 10 data rows minus 1 hold that gets superseded by its settlement (the "Общо" footer row is skipped).
    assert len(txns) == 9


def test_amount_converted_to_eur_on_or_after_adoption_date():
    txns = parse_statement_a(SAMPLE)
    matching = [t for t in txns if t.auth_code == "EEE555"]
    assert len(matching) == 1
    assert matching[0].currency == "EUR"
    assert matching[0].amount == Decimal("-10.00")


def test_amount_stays_bgn_before_adoption_date():
    txns = parse_statement_a(SAMPLE)
    matching = [t for t in txns if t.auth_code == "AAA111"]
    assert len(matching) == 1
    assert matching[0].currency == "BGN"


def test_hold_settlement_dedup_keeps_settled_row_with_merchant():
    txns = parse_statement_a(SAMPLE)
    matching = [t for t in txns if t.auth_code == "AAA111"]
    assert len(matching) == 1
    assert matching[0].is_settled is True
    assert matching[0].merchant == "BGR SOFIA TEST MERCHANT EOOD"
    assert matching[0].amount == Decimal("-25.00")


def test_unmatched_hold_kept_and_flagged_unsettled():
    txns = parse_statement_a(SAMPLE)
    matching = [t for t in txns if t.auth_code == "BBB222"]
    assert len(matching) == 1
    assert matching[0].is_settled is False
    assert matching[0].merchant is None


def test_atm_withdrawal_classified():
    txns = parse_statement_a(SAMPLE)
    matching = [t for t in txns if t.auth_code == "CCC333"]
    assert len(matching) == 1
    assert matching[0].transaction_type == TransactionType.ATM_WITHDRAWAL
    assert matching[0].amount == Decimal("-100.00")


def test_online_merchant_heuristic_classifies_glovo_as_online():
    txns = parse_statement_a(SAMPLE)
    matching = [t for t in txns if t.auth_code == "DDD444"]
    assert len(matching) == 1
    assert matching[0].transaction_type == TransactionType.CARD_ONLINE


def test_own_account_transfer_credit_amount_is_positive():
    txns = parse_statement_a(SAMPLE)
    matching = [t for t in txns if t.transaction_type == TransactionType.TRANSFER_OWN]
    assert len(matching) == 1
    assert matching[0].amount == Decimal("500.00")


def test_footer_total_row_is_skipped():
    txns = parse_statement_a(SAMPLE)
    assert all(t.description != "" for t in txns)
    assert not any(t.date is None for t in txns)


def test_duplicate_looking_transfers_get_distinct_external_ids():
    txns = parse_statement_a(SAMPLE)
    matching = [t for t in txns if t.description == "ВНОСКА ОТ ТРЕТО ЛИЦЕ"]
    assert len(matching) == 2
    assert matching[0].external_id != matching[1].external_id
    assert matching[0].amount == matching[1].amount == Decimal("300.00")


def test_duplicate_looking_transfers_both_survive_insert(db_conn):
    from budget_tracker import db

    txns = parse_statement_a(SAMPLE)
    db.insert_transactions(db_conn, txns)
    count = db_conn.execute(
        "SELECT count(*) FROM transactions WHERE description = 'ВНОСКА ОТ ТРЕТО ЛИЦЕ'"
    ).fetchone()[0]
    assert count == 2


def test_postuplenie_word_is_not_misread_as_pos_keyword():
    txns = parse_statement_a(SAMPLE)
    matching = [t for t in txns if t.description == "ПОСТЪПЛЕНИЕ ПО СМЕТКА"]
    assert len(matching) == 1
    assert matching[0].transaction_type == TransactionType.INCOMING_TRANSFER
    assert matching[0].is_settled is True


def test_reimport_is_idempotent_via_external_id(db_conn):
    from budget_tracker import db

    txns = parse_statement_a(SAMPLE)
    inserted_first = db.insert_transactions(db_conn, txns)
    inserted_second = db.insert_transactions(db_conn, txns)
    assert inserted_first == len(txns)
    assert inserted_second == len(txns)  # attempted, but all conflict on external_id
    count = db_conn.execute("SELECT count(*) FROM transactions").fetchone()[0]
    assert count == len(txns)
