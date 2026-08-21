from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import duckdb

from budget_tracker.models import Transaction

DEFAULT_DB_PATH = Path.home() / ".budget_tracker" / "budget.duckdb"

_MIGRATIONS: dict[int, str] = {
    1: """
        CREATE TYPE transaction_type AS ENUM (
            'atm_withdrawal', 'card_physical', 'card_online', 'transfer_own',
            'transfer_external', 'incoming_transfer', 'other'
        );

        CREATE SEQUENCE transactions_id_seq;

        CREATE TABLE transactions (
            id                BIGINT PRIMARY KEY DEFAULT nextval('transactions_id_seq'),
            date              DATE NOT NULL,
            amount            DECIMAL(12,2) NOT NULL,
            currency          VARCHAR NOT NULL DEFAULT 'BGN',
            description       VARCHAR NOT NULL,
            merchant          VARCHAR,
            account_label     VARCHAR,
            transaction_type  transaction_type NOT NULL,
            is_settled        BOOLEAN NOT NULL DEFAULT true,
            category          VARCHAR,
            category_group    VARCHAR,
            auth_code         VARCHAR,
            external_id       VARCHAR UNIQUE,
            source_file       VARCHAR,
            source_shape      VARCHAR,
            raw_row           VARCHAR,
            imported_at       TIMESTAMP DEFAULT current_timestamp
        );
    """,
    2: """
        CREATE TABLE categories (
            top_group VARCHAR NOT NULL,
            subgroup  VARCHAR,
            leaf      VARCHAR NOT NULL UNIQUE
        );
    """,
    3: """
        -- `date` is already a plain DATE column with no time component in the
        -- underlying data; some SQL client UIs render DATE values with a
        -- spurious "T00:00:00.000Z" suffix. This view formats it as a plain
        -- string so those clients display it as-is.
        CREATE VIEW transactions_display AS
        SELECT
            id,
            strftime(date, '%Y-%m-%d') AS date,
            amount,
            currency,
            description,
            merchant,
            account_label,
            transaction_type,
            is_settled,
            category,
            category_group,
            auth_code,
            external_id,
            source_file,
            source_shape,
            raw_row,
            imported_at
        FROM transactions;
    """,
}


def connect(path: str | Path = DEFAULT_DB_PATH) -> duckdb.DuckDBPyConnection:
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(path))
    ensure_schema(conn)
    return conn


def ensure_schema(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version    INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT current_timestamp
        );
        """
    )
    applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations").fetchall()}
    for version in sorted(_MIGRATIONS):
        if version in applied:
            continue
        conn.execute(_MIGRATIONS[version])
        conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", [version])


def insert_transaction(conn: duckdb.DuckDBPyConnection, txn: Transaction) -> int:
    return insert_transactions(conn, [txn])


def insert_transactions(conn: duckdb.DuckDBPyConnection, txns: Iterable[Transaction]) -> int:
    rows = [
        (
            t.date,
            t.amount,
            t.currency,
            t.description,
            t.merchant,
            t.account_label,
            t.transaction_type.value,
            t.is_settled,
            t.category,
            t.category_group,
            t.auth_code,
            t.external_id,
            t.source_file,
            t.source_shape,
            t.raw_row,
        )
        for t in txns
    ]
    if not rows:
        return 0
    conn.executemany(
        """
        INSERT INTO transactions (
            date, amount, currency, description, merchant, account_label,
            transaction_type, is_settled, category, category_group, auth_code,
            external_id, source_file, source_shape, raw_row
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (external_id) DO NOTHING
        """,
        rows,
    )
    return len(rows)


def load_categories(
    conn: duckdb.DuckDBPyConnection, rows: Iterable[tuple[str, str | None, str]]
) -> None:
    rows = list(rows)
    if not rows:
        return
    conn.execute("DELETE FROM categories")
    conn.executemany(
        "INSERT INTO categories (top_group, subgroup, leaf) VALUES (?, ?, ?)",
        rows,
    )
