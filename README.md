# budget-tracker

A personal budget tracking and analysis library. Imports bank statement exports,
stores transactions in an embedded [DuckDB](https://duckdb.org/) database, and
provides spend analysis by date, merchant, amount, and category. Designed to be
importable as a dependency (`import budget_tracker`) by a larger project.

## Install / develop

Environment management uses [uv](https://docs.astral.sh/uv/):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # if uv isn't installed yet
uv sync --all-groups                              # creates .venv/, installs deps
uv run pytest                                     # run the test suite
uv run ruff check .                               # lint
```

## What it does

- **Ingestion** (`budget_tracker.ingest`): parses HTML-table bank statement
  exports saved with a `.xls` extension (a common Bulgarian online-banking
  export format), in two known shapes:
  - `parse_statement_a` — account/card statements with merchant names, debit/credit
    columns, and transaction-type labels. Automatically de-duplicates card-authorization
    "hold" rows against their later settlement row so a purchase isn't double-counted.
  - `parse_statement_b` — a simpler card transaction log (date/time, type, auth code,
    amount only) that does **not** carry a merchant name.
- **Storage** (`budget_tracker.db`): an embedded DuckDB database (`transactions`,
  `categories` tables) with a small versioned-migration mechanism.
- **Categories** (`budget_tracker.categories`): loads a category taxonomy from JSON
  (see `src/budget_tracker/data/categories.json`), supporting flat lists, nested
  subgroup dicts, and single-string categories.
- **Analysis** (`budget_tracker.analysis`): spend by date range, by merchant, by
  amount, and category rollups, returned as `duckdb.DuckDBPyRelation` so callers
  can pull results as `.fetchall()`, `.df()` (pandas), or `.pl()` (polars) depending
  on what's installed downstream — this package itself has no pandas dependency.

### Classification caveats

- Online vs. physical card purchases (`card_online` vs. `card_physical`) is a
  **best-effort heuristic** based on a small merchant-keyword list
  (`budget_tracker.ingest.classify`) — the source bank data doesn't reliably
  separate the two. Extend the keyword list as needed.
- `parse_statement_b`'s source format never includes a merchant/store name, so
  merchant-based analysis is only meaningful for `parse_statement_a` imports.

## Not yet implemented

- Manual account operations (deposit/withdraw/transfer) — the original
  `Tracker` class stubs from this project's early skeleton are not carried
  forward; the current focus is statement import + analysis, not manual
  ledger entry.
- A CLI entry point.
- PyPI packaging/publish.

## Sensitive data

Real bank statement exports (`Reports/`) are `.gitignore`d and must never be
committed — they contain merchant names, partial account numbers, and personal
names from transfer counterparties. Tests use synthetic fixtures under
`tests/fixtures/` instead.
