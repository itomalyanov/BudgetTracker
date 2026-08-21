from __future__ import annotations

from datetime import date
from typing import Literal

import duckdb

# "Spend" analysis (as opposed to general cash flow) is scoped to ATM withdrawals
# and card payments only — inter-account transfers, incoming transfers, and loan
# repayments are money movement, not spend, and would otherwise skew merchant/
# amount rankings (e.g. an outgoing transfer showing up as the "top merchant").
_SPEND_TYPES = ("atm_withdrawal", "card_physical", "card_online")
_SPEND_TYPES_SQL = "(" + ", ".join(f"'{t}'" for t in _SPEND_TYPES) + ")"


def spend_by_date_range(
    conn: duckdb.DuckDBPyConnection,
    start: date,
    end: date,
    *,
    include_income: bool = False,
) -> duckdb.DuckDBPyRelation:
    """Daily net ATM/card spend (negative = outflow) between start and end, inclusive.

    `include_income` additionally nets in all non-spend transactions (transfers,
    loan payments, incoming credits) for a full cash-flow view of the same range.
    """
    if include_income:
        return conn.sql(
            """
            SELECT date, sum(amount) AS total
            FROM transactions
            WHERE date BETWEEN $start AND $end AND is_settled
            GROUP BY date
            ORDER BY date
            """,
            params={"start": start, "end": end},
        )
    return conn.sql(
        f"""
        SELECT date, sum(amount) AS total
        FROM transactions
        WHERE date BETWEEN $start AND $end
          AND is_settled
          AND transaction_type IN {_SPEND_TYPES_SQL}
        GROUP BY date
        ORDER BY date
        """,
        params={"start": start, "end": end},
    )


def spend_by_merchant(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
    *,
    top_n: int | None = None,
) -> duckdb.DuckDBPyRelation:
    """Total ATM/card spend per merchant; merchant is NULL for sources that don't carry it."""
    limit_clause = f"LIMIT {int(top_n)}" if top_n else ""
    return conn.sql(
        f"""
        SELECT merchant, sum(-amount) AS total_spent, count(*) AS num_transactions
        FROM transactions
        WHERE transaction_type IN {_SPEND_TYPES_SQL}
          AND is_settled
          AND ($start IS NULL OR date >= $start)
          AND ($end IS NULL OR date <= $end)
        GROUP BY merchant
        ORDER BY total_spent DESC
        {limit_clause}
        """,
        params={"start": start, "end": end},
    )


def spend_by_amount(
    conn: duckdb.DuckDBPyConnection,
    min_amount: float | None = None,
    max_amount: float | None = None,
) -> duckdb.DuckDBPyRelation:
    """Individual ATM/card spend transactions whose amount falls within the given bounds."""
    return conn.sql(
        f"""
        SELECT id, date, merchant, description, -amount AS spent
        FROM transactions
        WHERE transaction_type IN {_SPEND_TYPES_SQL}
          AND amount < 0
          AND is_settled
          AND ($min_amount IS NULL OR -amount >= $min_amount)
          AND ($max_amount IS NULL OR -amount <= $max_amount)
        ORDER BY spent DESC
        """,
        params={"min_amount": min_amount, "max_amount": max_amount},
    )


def category_rollup(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
    *,
    group_by: Literal["group", "leaf"] = "group",
) -> duckdb.DuckDBPyRelation:
    """Total ATM/card spend rolled up by category group or leaf category."""
    column = "category_group" if group_by == "group" else "category"
    return conn.sql(
        f"""
        SELECT {column} AS category, sum(-amount) AS total_spent
        FROM transactions
        WHERE transaction_type IN {_SPEND_TYPES_SQL}
          AND is_settled
          AND ($start IS NULL OR date >= $start)
          AND ($end IS NULL OR date <= $end)
        GROUP BY {column}
        ORDER BY total_spent DESC
        """,
        params={"start": start, "end": end},
    )
