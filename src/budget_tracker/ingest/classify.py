from __future__ import annotations

from budget_tracker.ingest._parsing import contains_word
from budget_tracker.models import TransactionType

_ATM_KEYWORDS = ("ТЕГЛЕНЕ НА ATM", "ТЕГЛЕНЕ НА БАНКОМАТ", "БАНКОМАТ")
_POS_KEYWORDS = ("ПОС",)
_OWN_TRANSFER_KEYWORDS = ("ТРАНСФЕР СОБСТВЕНИ СМЕТКИ", "ТРАНСФЕР МЕЖДУ СВОИ СМЕТКИ")
_TRANSFER_KEYWORDS = ("ПАРИЧЕН ПРЕВОД", "КРЕДИТЕН ПРЕВОД")

# Best-effort only: this bank export does not reliably distinguish online vs.
# physical card purchases. Extend this list as more real merchant names are seen.
_ONLINE_MERCHANT_KEYWORDS = (
    "GLOVO",
    "AMAZON",
    "NETFLIX",
    "UBER",
    "BOLT",
    "SPOTIFY",
    "STEAM",
    "APPLE.COM",
    "GOOGLE",
    "PAYPAL",
)


def classify(
    description: str,
    transaction_type_field: str,
    *,
    merchant: str | None = None,
    is_credit: bool = False,
) -> TransactionType:
    """Best-effort classification of a Bulgarian bank-statement row.

    `Вид на трансакцията` (transaction_type_field) is often blank for pending
    card-authorization holds and some loan-payment rows, so classification
    primarily relies on Bulgarian keywords in the free-text description.
    """
    text = f"{description} {transaction_type_field}".upper()

    if any(keyword in text for keyword in _ATM_KEYWORDS):
        return TransactionType.ATM_WITHDRAWAL

    if any(contains_word(text, keyword) for keyword in _POS_KEYWORDS):
        haystack = f"{description} {merchant or ''}".upper()
        if any(keyword in haystack for keyword in _ONLINE_MERCHANT_KEYWORDS):
            return TransactionType.CARD_ONLINE
        return TransactionType.CARD_PHYSICAL

    if any(keyword in text for keyword in _OWN_TRANSFER_KEYWORDS):
        return TransactionType.TRANSFER_OWN

    if any(keyword in text for keyword in _TRANSFER_KEYWORDS):
        return TransactionType.INCOMING_TRANSFER if is_credit else TransactionType.TRANSFER_EXTERNAL

    return TransactionType.OTHER
