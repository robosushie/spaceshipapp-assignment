import pytest

from src.agent.schema import logistics_ddl
from src.agent.sql_guard import SqlRejected, checked_sql


def test_schema_lists_the_book_and_hides_auth_tables() -> None:
    ddl = logistics_ddl()
    for table in ("clients", "warehouses", "carriers", "products", "orders"):
        assert f"CREATE TABLE {table}" in ddl
    assert "users" not in ddl
    assert "refresh_tokens" not in ddl
    assert "2025-12-30" in ddl


def test_guard_accepts_one_select_on_orders() -> None:
    sql = checked_sql("SELECT count(*) AS orders FROM orders")
    assert "orders" in sql.lower()
    assert "select" in sql.lower()


def test_guard_rejects_insert_without_repair() -> None:
    with pytest.raises(SqlRejected) as caught:
        checked_sql("INSERT INTO orders (order_id) VALUES ('x')")
    assert caught.value.repair is False


def test_guard_rejects_two_statements() -> None:
    with pytest.raises(SqlRejected) as caught:
        checked_sql("SELECT 1; SELECT 2")
    assert caught.value.repair is True


def test_guard_rejects_users_without_repair() -> None:
    with pytest.raises(SqlRejected) as caught:
        checked_sql("SELECT email FROM users")
    assert caught.value.repair is False
