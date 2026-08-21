from __future__ import annotations

import json
import re
from pathlib import Path

from budget_tracker.currency import convert_to_local_currency
from budget_tracker.ingest._parsing import (
    contains_word,
    extract_auth_code,
    make_external_id,
    parse_bg_amount,
    parse_bg_date,
)
from budget_tracker.ingest.classify import classify
from budget_tracker.ingest.html_table import parse_html_tables
from budget_tracker.models import Transaction

_HEADER_ROW_INDEX = 2
_DATA_START_INDEX = 3
_SETTLED_POS_MARKER = "ПЛАЩАНЕ НА ПОС"
_POS_MARKER = "ПОС"
_DATE_RE = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")

_REQUIRED_COLUMNS = (
    "Дата",
    "Основание",
    "Наредител/Получател",
    "Вид на трансакцията",
    "Дебит BGN",
    "Кредит BGN",
)


def parse_statement_a(path: str | Path, *, account_label: str | None = None) -> list[Transaction]:
    """Parses an account/card statement export (10-column HTML table saved as .xls).

    Auth-hold rows (bare `ПОС` entries with no merchant/type, preceding settlement)
    are de-duplicated against their matching `ПЛАЩАНЕ НА ПОС` settlement row via
    the shared auth code, so a purchase isn't counted twice.
    """
    tables = parse_html_tables(path)
    if not tables or len(tables[0]) <= _DATA_START_INDEX:
        return []

    table = tables[0]
    if account_label is None:
        account_label = " ".join(cell for cell in table[0] if cell).strip() or None

    header = table[_HEADER_ROW_INDEX]
    idx = {name: i for i, name in enumerate(header)}
    if not all(name in idx for name in _REQUIRED_COLUMNS):
        raise ValueError(f"Unrecognized Shape-A header in {path}: {header}")

    source_file = Path(path).name
    candidates: list[tuple[Transaction, str | None, bool]] = []
    settled_auth_codes: set[str] = set()
    seen_counts: dict[tuple[str, ...], int] = {}

    for row in table[_DATA_START_INDEX:]:
        if len(row) <= max(idx.values()):
            continue

        date_str = row[idx["Дата"]].strip()
        if not _DATE_RE.match(date_str):
            continue  # skips summary/total footer rows (e.g. "Общо")

        description = row[idx["Основание"]].strip()
        merchant = row[idx["Наредител/Получател"]].strip() or None
        tx_type_field = row[idx["Вид на трансакцията"]].strip()
        debit_str = row[idx["Дебит BGN"]].strip()
        credit_str = row[idx["Кредит BGN"]].strip()

        is_credit = bool(credit_str)
        amount_str = credit_str if is_credit else debit_str
        if not amount_str:
            continue

        amount = parse_bg_amount(amount_str)
        if not is_credit:
            amount = -amount

        txn_date = parse_bg_date(date_str)
        amount, currency = convert_to_local_currency(amount, txn_date)

        description_upper = description.upper()
        auth_code = extract_auth_code(description)
        is_hold = (
            contains_word(description_upper, _POS_MARKER)
            and _SETTLED_POS_MARKER not in description_upper
            and not tx_type_field
        )
        if not is_hold and auth_code and _SETTLED_POS_MARKER in description_upper:
            settled_auth_codes.add(auth_code)

        external_id_key = (account_label or "", date_str, description, amount_str, tx_type_field)
        ordinal = seen_counts.get(external_id_key, 0)
        seen_counts[external_id_key] = ordinal + 1
        external_id = (
            make_external_id(*external_id_key)
            if ordinal == 0
            else make_external_id(*external_id_key, str(ordinal))
        )

        txn = Transaction(
            date=txn_date,
            amount=amount,
            currency=currency,
            description=description,
            transaction_type=classify(
                description, tx_type_field, merchant=merchant, is_credit=is_credit
            ),
            merchant=merchant,
            account_label=account_label,
            is_settled=not is_hold,
            auth_code=auth_code,
            source_file=source_file,
            source_shape="A",
            raw_row=json.dumps(dict(zip(header, row)), ensure_ascii=False),
            external_id=external_id,
        )
        candidates.append((txn, auth_code, is_hold))

    return [
        txn
        for txn, auth_code, is_hold in candidates
        if not (is_hold and auth_code in settled_auth_codes)
    ]
