"""Migrate, then load the shipping book the first time the orders table is empty."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def should_seed(order_count: int) -> bool:
    return order_count == 0


def order_count() -> int:
    from sqlalchemy import text

    from src.lib.db import engine

    with engine.connect() as connection:
        count = connection.execute(text("SELECT COUNT(*) FROM orders")).scalar_one()
    return int(count)


def main() -> None:
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=ROOT, check=True)
    if not should_seed(order_count()):
        return
    from scripts.bootstrap.run import load_json

    load_json()


if __name__ == "__main__":
    main()
