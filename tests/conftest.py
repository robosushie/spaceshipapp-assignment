import os
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

_base_url = os.environ["DATABASE_URL"]
_server = _base_url.rsplit("/", 1)[0].replace("postgresql+psycopg://", "postgresql://")
_admin_url = f"{_server}/postgres"
_test_db = "spaceship_test"
with psycopg.connect(_admin_url, autocommit=True) as connection:
    exists = connection.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s",
        (_test_db,),
    ).fetchone()
    if exists is None:
        connection.execute(f"CREATE DATABASE {_test_db}")

os.environ["DATABASE_URL"] = _base_url.rsplit("/", 1)[0] + f"/{_test_db}"

from src.lib.config import get_settings  # noqa: E402

get_settings.cache_clear()
command.upgrade(Config(str(ROOT / "alembic.ini")), "head")

from src.lib.db import engine  # noqa: E402
from src.lib.rate_limit import login_limiter  # noqa: E402
from src.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_database() -> Iterator[None]:
    login_limiter.reset()
    yield
    with engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE refresh_tokens, users, orders, products, carriers, "
                "warehouses, clients RESTART IDENTITY CASCADE"
            )
        )
    login_limiter.reset()


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
