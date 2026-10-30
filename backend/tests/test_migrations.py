"""Unit tests to verify schema definitions and table constraints."""

import pytest
from sqlalchemy import create_engine, inspect

from app.models import Base


def test_models_metadata_has_all_expected_tables():
    """Verify SQLAlchemy metadata contains all 10 required tables."""
    expected_tables = {
        "users",
        "accounts",
        "stocks",
        "price_bars",
        "orders",
        "holdings",
        "transactions",
        "watchlist_items",
        "portfolio_snapshots",
        "sim_state",
    }
    registered_tables = set(Base.metadata.tables.keys())
    assert expected_tables.issubset(registered_tables), (
        f"Missing tables in Base.metadata: {expected_tables - registered_tables}"
    )


def test_clean_database_schema_creation_and_column_types():
    """Verify schema applies cleanly on an empty database with NUMERIC types."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    inspector = inspect(engine)
    db_tables = set(inspector.get_table_names())

    expected_tables = [
        "users",
        "accounts",
        "stocks",
        "price_bars",
        "orders",
        "holdings",
        "transactions",
        "watchlist_items",
        "portfolio_snapshots",
        "sim_state",
    ]

    for table in expected_tables:
        assert table in db_tables, f"Table {table} was not created"
        columns = {col["name"]: col for col in inspector.get_columns(table)}
        assert "id" in columns, f"Table {table} missing 'id' primary key"

    # Verify money columns are NUMERIC
    account_cols = {col["name"]: col for col in inspector.get_columns("accounts")}
    assert "cash_balance" in account_cols
    assert "NUMERIC" in str(account_cols["cash_balance"]["type"]).upper()

    order_cols = {col["name"]: col for col in inspector.get_columns("orders")}
    assert "limit_price" in order_cols
    assert "NUMERIC" in str(order_cols["limit_price"]["type"]).upper()

    price_cols = {col["name"]: col for col in inspector.get_columns("price_bars")}
    assert "close" in price_cols
    assert "NUMERIC" in str(price_cols["close"]["type"]).upper()
