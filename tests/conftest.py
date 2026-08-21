from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from budget_tracker import db
from budget_tracker.categories import CategoryTaxonomy

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def db_conn() -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(":memory:")
    db.ensure_schema(conn)
    yield conn
    conn.close()


@pytest.fixture
def taxonomy() -> CategoryTaxonomy:
    return CategoryTaxonomy.default()
