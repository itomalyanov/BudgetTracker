from __future__ import annotations

import json
import re
from pathlib import Path

from budget_tracker.currency import convert_to_local_currency
from budget_tracker.ingest._parsing import (
    extract_auth_code,
    make_external_id,
    parse_bg_amount,
    parse_bg_datetime,
)
from budget_tracker.ingest.classify import classify
from budget_tracker.ingest.html_table import parse_html_tables
from budget_tracker.models import Transaction

_HEADER_ROW_INDEX = 1
_DATA_START_INDEX = 2
_DATETIME_COLUMN = "Дата и час на извършване"
_TYPE_COLUMN = "Вид на транзакцията"
_PLACE_COLUMN = "Място на извършване"
_AMOUNT_PREFIX = "Сума"
_DATETIME_RE = re.compile(r"^\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}$")


def parse_statement_b(path: str | Path, *, account_label: str | None = None) -> list[Transaction]:
    """Parses a card transaction log export (4-column HTML table saved as .xls).

    This shape never carries a merchant/store name (only an auth code and a
    generic transaction type), so `merchant` is always None on the result.
    """
    tables = parse_html_tables(path)
    if not tables or len(tables[0]) <= _DATA_START_INDEX:
        return []

    table = tables[0]
    if account_label is None:
        account_label = " ".join(cell for cell in table[0] if cell).strip() or None

    header = table[_HEADER_ROW_INDEX]
    idx = {name: i for i, name in enumerate(header)}
    amount_col = next((name for name in header if name.startswith(_AMOUNT_PREFIX)), None)
    if (
        _DATETIME_COLUMN not in idx
        or _TYPE_COLUMN not in idx
        or _PLACE_COLUMN not in idx
        or amount_col is None
    ):
        raise ValueError(f"Unrecognized Shape-B header in {path}: {header}")

    required_idx = (idx[_DATETIME_COLUMN], idx[_TYPE_COLUMN], idx[_PLACE_COLUMN], idx[amount_col])
    source_file = Path(path).name
    transactions: list[Transaction] = []
    seen_counts: dict[tuple[str, ...], int] = {}

    for row in table[_DATA_START_INDEX:]:
        if len(row) <= max(required_idx):
            continue

        datetime_str = row[idx[_DATETIME_COLUMN]].strip()
        if not _DATETIME_RE.match(datetime_str):
            continue  # skips summary/total footer rows

        tx_type_field = row[idx[_TYPE_COLUMN]].strip()
        place = row[idx[_PLACE_COLUMN]].strip()
        amount_str = row[idx[amount_col]].strip()
        if not amount_str:
            continue

        amount = -parse_bg_amount(amount_str)
        txn_date = parse_bg_datetime(datetime_str).date()
        amount, currency = convert_to_local_currency(amount, txn_date)
        description = f"{tx_type_field} {place}".strip()
        auth_code = extract_auth_code(place) or extract_auth_code(tx_type_field)

        external_id_key = (account_label or "", datetime_str, tx_type_field, place, amount_str)
        ordinal = seen_counts.get(external_id_key, 0)
        seen_counts[external_id_key] = ordinal + 1
        external_id = (
            make_external_id(*external_id_key)
            if ordinal == 0
            else make_external_id(*external_id_key, str(ordinal))
        )

        transactions.append(
            Transaction(
                date=txn_date,
                amount=amount,
                currency=currency,
                description=description,
                transaction_type=classify(
                    description, tx_type_field, merchant=None, is_credit=False
                ),
                merchant=None,
                account_label=account_label,
                auth_code=auth_code,
                source_file=source_file,
                source_shape="B",
                raw_row=json.dumps(dict(zip(header, row)), ensure_ascii=False),
                external_id=external_id,
            )
        )

    return transactions
