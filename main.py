"""Example queries against the local budget_tracker DuckDB database.

Run `uv run python scripts/load_reports.py` first to populate budget.duckdb
from Reports/, then:

    uv run python main.py
    uv run python main.py sopharmacy
    uv run python main.py lidl
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

from budget_tracker import analysis, db

DB_PATH = Path(__file__).parent / "budget.duckdb"


def print_all_categories(conn: duckdb.DuckDBPyConnection) -> None:
    """Every category in the taxonomy (loaded from categories.json), as group > leaf."""
    print("=== All categories ===")
    rows = conn.execute(
        "SELECT top_group, subgroup, leaf FROM categories ORDER BY top_group, subgroup, leaf"
    ).fetchall()
    for top_group, subgroup, leaf in rows:
        label = f"{top_group} > {subgroup} > {leaf}" if subgroup else f"{top_group} > {leaf}"
        print(" ", label)


def print_category_rollup(conn: duckdb.DuckDBPyConnection) -> None:
    """Total ATM/card spend per category group, including whatever is still uncategorized."""
    print("\n=== Spend by category group ===")
    for category, total in analysis.category_rollup(conn, group_by="group").fetchall():
        print(f"  {category or '(uncategorized)':<15} {total:>10} BGN")


def print_spend_by_date_range(conn: duckdb.DuckDBPyConnection) -> None:
    """Total spend for the last 30 days present in the data."""
    end = conn.execute("SELECT max(date) FROM transactions").fetchone()[0]
    if end is None:
        return
    start = end.replace(day=1)
    print(f"\n=== Spend by day, {start} to {end} ===")
    for date, total in analysis.spend_by_date_range(conn, start, end).fetchall():
        print(f"  {date}  {total:>8} BGN")


def print_merchant_search(conn: duckdb.DuckDBPyConnection, keyword: str) -> None:
    """All spend matching a keyword.

    Searches both `merchant` and `description`: some report shapes never fill
    in `merchant` and only carry the store name inside the free-text
    description, so a merchant-only search can silently miss real matches
    (this is exactly why "sopharmacy" wouldn't show up if you only checked
    `merchant`).
    """
    print(f"\n=== Transactions matching '{keyword}' ===")
    rows = conn.execute(
        """
        SELECT date, merchant, description, -amount AS spent
        FROM transactions
        WHERE (merchant ILIKE '%' || $kw || '%' OR description ILIKE '%' || $kw || '%')
          AND amount < 0
        ORDER BY date
        """,
        {"kw": keyword},
    ).fetchall()
    if not rows:
        print("  (no matches)")
        return
    for date, merchant, description, spent in rows:
        print(f"  {date}  {spent:>8.2f} BGN   {merchant or description}")
    total = sum(r[3] for r in rows)
    print(f"  --- total: {total:.2f} BGN across {len(rows)} transaction(s) ---")


def main() -> None:
    if not DB_PATH.exists():
        print(f"No database found at {DB_PATH}.")
        print("Run `uv run python scripts/load_reports.py` first to load Reports/ into it.")
        return

    conn = db.connect(DB_PATH)

    print_all_categories(conn)
    print_category_rollup(conn)
    print_spend_by_date_range(conn)

    keyword = sys.argv[1] if len(sys.argv) > 1 else "sopharmacy"
    print_merchant_search(conn, keyword)

    conn.close()


if __name__ == "__main__":
    main()
