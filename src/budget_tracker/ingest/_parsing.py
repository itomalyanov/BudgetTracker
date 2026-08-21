from __future__ import annotations

import hashlib
import re
from datetime import date as Date
from datetime import datetime
from decimal import Decimal

_AUTH_CODE_RE = re.compile(r"Авт\.\s*код:\s*([A-Za-z0-9]+)")


def parse_bg_amount(raw: str) -> Decimal:
    """Parses a Bulgarian-formatted amount (comma decimal, optional dot thousands separator)."""
    cleaned = raw.replace("\xa0", "").replace(" ", "").replace(".", "").replace(",", ".")
    return Decimal(cleaned)


def parse_bg_date(raw: str) -> Date:
    return datetime.strptime(raw.strip(), "%d.%m.%Y").date()


def parse_bg_datetime(raw: str) -> datetime:
    return datetime.strptime(raw.strip(), "%d.%m.%Y %H:%M")


def extract_auth_code(text: str) -> str | None:
    match = _AUTH_CODE_RE.search(text)
    return match.group(1) if match else None


def contains_word(text: str, word: str) -> bool:
    """Whole-word substring match (word-boundary aware, Cyrillic included).

    Plain `in` matching is unsafe for short keywords like "ПОС" ("POS"),
    which is also a substring of unrelated words such as "ПОСТЪПЛЕНИЕ"
    (deposit) or "ПОСРЕДНИЧЕСТВО" (brokerage).
    """
    return re.search(rf"\b{re.escape(word)}\b", text) is not None


def make_external_id(*parts: str) -> str:
    joined = "|".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:32]
