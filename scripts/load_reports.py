"""Loads every report in Reports/ into a local DuckDB file and prints some
analysis queries against it. Not part of the installable package — a manual
dev/exploration script that operates on the gitignored Reports/ folder.

Usage: uv run python scripts/load_reports.py
"""

from __future__ import annotations

from pathlib import Path

from budget_tracker import analysis, db
from budget_tracker.categories import CategoryTaxonomy
from budget_tracker.categorize import apply_categories
from budget_tracker.ingest.html_table import parse_html_tables
from budget_tracker.ingest.statement_a import parse_statement_a
from budget_tracker.ingest.statement_b import parse_statement_b
from budget_tracker.models import Transaction

REPORTS_DIR = Path(__file__).parent.parent / "Reports"
DB_PATH = Path(__file__).parent.parent / "budget.duckdb"


def detect_and_parse(path: Path) -> list[Transaction]:
    tables = parse_html_tables(path)
    if not tables:
        return []
    table = tables[0]
    if len(table) > 2 and "Дата" in table[2] and "Дебит BGN" in table[2]:
        return parse_statement_a(path)
    if len(table) > 1 and "Дата и час на извършване" in table[1]:
        return parse_statement_b(path)
    print(f"  ! could not detect shape for {path.name}, skipping")
    return []


def main() -> None:
    if not REPORTS_DIR.exists():
        print(f"No Reports/ folder found at {REPORTS_DIR}")
        return

    conn = db.connect(DB_PATH)
    taxonomy = CategoryTaxonomy.default()
    db.load_categories(conn, taxonomy.as_rows())

    report_files = sorted(REPORTS_DIR.glob("*.xls"))
    print(f"Found {len(report_files)} report file(s) in {REPORTS_DIR}\n")

    total_inserted = 0
    for path in report_files:
        txns = detect_and_parse(path)
        inserted = db.insert_transactions(conn, txns)
        total_inserted += inserted
        print(f"  {path.name}: parsed {len(txns)} transaction(s)")

    total_rows = conn.execute("SELECT count(*) FROM transactions").fetchone()[0]
    print(f"\nTotal rows attempted this run: {total_inserted}")
    print(f"Total distinct rows now in {DB_PATH.name}: {total_rows}")

    categorized = apply_categories(conn, taxonomy)
    print(f"Newly categorized this run: {categorized}\n")

    date_bounds = conn.execute("SELECT min(date), max(date) FROM transactions").fetchone()
    start, end = date_bounds
    if start is None:
        print("No transactions in the database yet.")
        return

    print(f"=== Spend by date range ({start} to {end}) ===")
    for row in analysis.spend_by_date_range(conn, start, end).fetchall()[:10]:
        print(" ", row)

    print("\n=== Top merchants by spend ===")
    for row in analysis.spend_by_merchant(conn, top_n=10).fetchall():
        print(" ", row)

    print("\n=== Category rollup ===")
    for row in analysis.category_rollup(conn, group_by="group").fetchall():
        print(" ", row)

    print("\n=== Largest individual transactions ===")
    for row in analysis.spend_by_amount(conn, min_amount=100).fetchall()[:10]:
        print(" ", row)

    conn.close()


if __name__ == "__main__":
    main()
