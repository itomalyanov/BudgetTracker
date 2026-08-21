from __future__ import annotations

from datetime import date as Date
from decimal import ROUND_HALF_UP, Decimal

# Bulgaria's fixed currency-board peg to the euro (in place since 1999), used
# as the official conversion rate for euro adoption.
BGN_TO_EUR_RATE = Decimal("1.95583")

# Bulgaria adopted the euro on this date. Bank statements may continue to
# print BGN-denominated amounts after this date (as observed in real exports),
# so amounts dated on/after this point are converted rather than trusted as-is.
EUR_ADOPTION_DATE = Date(2026, 1, 1)


def convert_to_local_currency(amount: Decimal, transaction_date: Date) -> tuple[Decimal, str]:
    """Returns (amount, currency): BGN unchanged before EUR_ADOPTION_DATE,
    converted to EUR at the fixed peg rate from EUR_ADOPTION_DATE onward.
    """
    if transaction_date < EUR_ADOPTION_DATE:
        return amount, "BGN"
    eur_amount = (amount / BGN_TO_EUR_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return eur_amount, "EUR"
