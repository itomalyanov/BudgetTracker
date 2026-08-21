from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as Date
from decimal import Decimal
from enum import Enum


class TransactionType(str, Enum):
    ATM_WITHDRAWAL = "atm_withdrawal"
    CARD_PHYSICAL = "card_physical"
    CARD_ONLINE = "card_online"
    TRANSFER_OWN = "transfer_own"
    TRANSFER_EXTERNAL = "transfer_external"
    INCOMING_TRANSFER = "incoming_transfer"
    OTHER = "other"


@dataclass(slots=True)
class Transaction:
    date: Date
    amount: Decimal
    description: str
    transaction_type: TransactionType
    currency: str = "BGN"
    merchant: str | None = None
    account_label: str | None = None
    is_settled: bool = True
    category: str | None = None
    category_group: str | None = None
    auth_code: str | None = None
    external_id: str | None = None
    source_file: str | None = None
    source_shape: str | None = None
    raw_row: str | None = None
    id: int | None = field(default=None, compare=False)
