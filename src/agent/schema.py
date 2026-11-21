from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable
from sqlmodel import SQLModel

import src.models  # noqa: F401

BOOK_AS_OF = "2025-12-30"

LOGISTICS_TABLES = ("clients", "warehouses", "carriers", "products", "orders")
ALLOWED_TABLES = frozenset(LOGISTICS_TABLES)
SECRET_TABLES = frozenset({"users", "refresh_tokens"})


def logistics_ddl() -> str:
    dialect = postgresql.dialect()
    statements = [
        "-- The shipping book ends on 2025-12-30. Treat that date as today.",
        "-- orders.status is one of: delivered, delayed, in_transit, exception, canceled.",
        "-- order_value_usd equals quantity * unit_price_usd. promo_discount_pct is not applied.",
        "-- Region is warehouses.region. orders has no region column.",
    ]
    for name in LOGISTICS_TABLES:
        compiled = str(CreateTable(SQLModel.metadata.tables[name]).compile(dialect=dialect)).strip()
        statements.append(compiled + ";")
    return "\n\n".join(statements)
