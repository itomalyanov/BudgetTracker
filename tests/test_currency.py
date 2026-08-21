from __future__ import annotations

from datetime import date
from decimal import Decimal

from budget_tracker.currency import convert_to_local_currency


def test_pre_2026_amount_stays_bgn_unchanged():
    amount, currency = convert_to_local_currency(Decimal("-19.56"), date(2025, 12, 31))
    assert currency == "BGN"
    assert amount == Decimal("-19.56")


def test_on_adoption_date_converts_to_eur():
    amount, currency = convert_to_local_currency(Decimal("-19.56"), date(2026, 1, 1))
    assert currency == "EUR"
    assert amount == Decimal("-10.00")


def test_after_adoption_date_converts_to_eur():
    amount, currency = convert_to_local_currency(Decimal("-19.56"), date(2026, 6, 15))
    assert currency == "EUR"
    assert amount == Decimal("-10.00")


def test_positive_amount_converts_correctly():
    amount, currency = convert_to_local_currency(Decimal("1955.83"), date(2026, 1, 1))
    assert currency == "EUR"
    assert amount == Decimal("1000.00")
