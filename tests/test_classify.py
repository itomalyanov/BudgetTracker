from __future__ import annotations

from budget_tracker.ingest.classify import classify
from budget_tracker.models import TransactionType


def test_bare_pos_keyword_classified_as_card_physical():
    assert classify("111111xxxxxx2222 ПОС", "КАРТОВА ОПЕРАЦИЯ") == TransactionType.CARD_PHYSICAL


def test_postuplenie_word_is_not_matched_as_pos_substring():
    result = classify("ПОСТЪПЛЕНИЕ ПО СМЕТКА", "ПАРИЧЕН ПРЕВОД", is_credit=True)
    assert result == TransactionType.INCOMING_TRANSFER


def test_posrednichestvo_word_is_not_matched_as_pos_substring():
    result = classify("ТАКСА ПОСРЕДНИЧЕСТВО", "ПАРИЧЕН ПРЕВОД", is_credit=False)
    assert result == TransactionType.TRANSFER_EXTERNAL
