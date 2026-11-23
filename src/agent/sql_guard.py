from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import text
from sqlglot import exp, parse
from sqlglot.errors import SqlglotError
from sqlmodel import Session

from src.agent.schema import ALLOWED_TABLES, SECRET_TABLES

_ROW_LIMIT = 200
_BLOCKED_FUNCTIONS = frozenset(
    {
        "pg_sleep",
        "pg_read_file",
        "pg_read_binary_file",
        "pg_ls_dir",
        "lo_import",
        "lo_export",
        "dblink",
        "dblink_exec",
    }
)
_WRITE = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter, exp.Create, exp.Command)
_QUERY = (exp.Select, exp.Union, exp.Intersect, exp.Except)


class SqlRejected(Exception):
    def __init__(self, message: str, *, repair: bool) -> None:
        super().__init__(message)
        self.repair = repair


def checked_sql(sql: str) -> str:
    try:
        statements = [item for item in parse(sql, read="postgres") if item is not None]
    except SqlglotError as exc:
        raise SqlRejected(f"SQL could not be parsed: {exc}", repair=True) from exc
    if len(statements) != 1:
        repair = not any(_is_write(item) for item in statements)
        raise SqlRejected("Exactly one SELECT is allowed.", repair=repair)
    statement = statements[0]
    if _is_write(statement) or statement.find(*_WRITE) is not None:
        raise SqlRejected("Only a single SELECT is allowed.", repair=False)
    if not isinstance(statement, _QUERY):
        raise SqlRejected("Only a single SELECT is allowed.", repair=False)
    if isinstance(statement, exp.Select) and statement.args.get("into") is not None:
        raise SqlRejected("Only a single SELECT is allowed.", repair=False)
    _reject_functions(statement)
    _reject_tables(statement)
    return statement.sql(dialect="postgres")


def run_select(session: Session, sql: str) -> list[dict[str, str]]:
    safe = checked_sql(sql)
    wrapped = f"SELECT * FROM ({safe}) AS q LIMIT {_ROW_LIMIT}"
    try:
        session.execute(text("SET LOCAL statement_timeout = '5s'"))
        session.execute(text("SET LOCAL transaction_read_only = on"))
        session.execute(text(f"EXPLAIN {safe}"))
        result = session.execute(text(wrapped))
        return [{str(key): _cell(value) for key, value in row.items()} for row in result.mappings()]
    except SqlRejected:
        raise
    except Exception as exc:
        session.rollback()
        raise SqlRejected(_error_text(exc), repair=True) from exc


def _is_write(statement: exp.Expr) -> bool:
    return isinstance(statement, _WRITE) or statement.find(*_WRITE) is not None


def _reject_functions(statement: exp.Expr) -> None:
    for function in statement.find_all(exp.Func):
        name = _function_name(function)
        if name in _BLOCKED_FUNCTIONS:
            raise SqlRejected("That function is not allowed.", repair=False)


def _function_name(function: exp.Func) -> str:
    if isinstance(function, exp.Anonymous):
        return str(function.this).lower()
    sql_name = getattr(function, "sql_name", None)
    if callable(sql_name):
        return str(sql_name()).lower()
    return ""


def _reject_tables(statement: exp.Expr) -> None:
    cte_names = {cte.alias_or_name.lower() for cte in statement.find_all(exp.CTE)}
    tables = {table.name.lower() for table in statement.find_all(exp.Table) if table.name}
    referenced = tables - cte_names
    if referenced & SECRET_TABLES:
        raise SqlRejected("That table is not available.", repair=False)
    unknown = referenced - ALLOWED_TABLES
    if unknown:
        raise SqlRejected(
            f"Unknown tables: {', '.join(sorted(unknown))}.",
            repair=True,
        )


def _cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        if value == value.to_integral():
            return str(int(value))
        return f"{value.quantize(Decimal('0.01')):.2f}"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _error_text(exc: Exception) -> str:
    origin = getattr(exc, "orig", None)
    text_value = str(origin or exc).split("\n", maxsplit=1)[0]
    return text_value[:500]
