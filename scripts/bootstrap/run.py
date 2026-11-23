"""Export the shipping book to JSON and load it into Postgres."""

from __future__ import annotations

import csv
import json
import sys
from collections.abc import Iterable, Mapping, Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlmodel import Session, select

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "docs" / "manuals" / "mock_logistics_data.csv"
DATA_DIR = Path(__file__).resolve().parent / "data"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.enums.identity import UserRole  # noqa: E402
from src.enums.orders import OrderStatus  # noqa: E402
from src.lib.config import get_settings  # noqa: E402
from src.lib.db import engine  # noqa: E402
from src.lib.security import hash_password  # noqa: E402
from src.models.catalog.carrier import Carrier  # noqa: E402
from src.models.catalog.client import Client  # noqa: E402
from src.models.catalog.product import Product  # noqa: E402
from src.models.catalog.warehouse import Warehouse  # noqa: E402
from src.models.identity.user import User  # noqa: E402
from src.models.orders.order import Order  # noqa: E402
from src.services.identity.auth import normalize_email  # noqa: E402


def _write(name: str, rows: Sequence[Mapping[str, object]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / name
    path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")


def _read_csv() -> list[dict[str, str]]:
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def export_json() -> None:
    rows = _read_csv()
    clients = [{"client_id": client_id} for client_id in sorted({row["client_id"] for row in rows})]
    warehouses = sorted({(row["warehouse"], row["region"], row["origin_city"]) for row in rows})
    carriers = [{"name": name} for name in sorted({row["carrier"] for row in rows})]
    products = sorted({(row["sku"], row["product_category"]) for row in rows})
    orders = [
        {
            "order_id": row["order_id"],
            "client_id": row["client_id"],
            "warehouse_code": row["warehouse"],
            "carrier_name": row["carrier"],
            "sku": row["sku"],
            "destination_city": row["destination_city"],
            "status": row["status"],
            "order_date": row["order_date"],
            "delivery_date": row["delivery_date"] or None,
            "quantity": int(row["quantity"]),
            "unit_price_usd": row["unit_price_usd"],
            "order_value_usd": row["order_value_usd"],
            "is_promo": row["is_promo"] == "1",
            "promo_discount_pct": int(row["promo_discount_pct"]),
        }
        for row in rows
    ]
    orders.sort(key=lambda item: str(item["order_id"]))
    _write("clients.json", clients)
    _write(
        "warehouses.json",
        [
            {"code": code, "region": region, "origin_city": origin}
            for code, region, origin in warehouses
        ],
    )
    _write("carriers.json", carriers)
    _write("products.json", [{"sku": sku, "category": category} for sku, category in products])
    _write("orders.json", orders)


def _load_json(name: str) -> list[dict[str, object]]:
    payload = json.loads((DATA_DIR / name).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise SystemExit(f"{name} must be a JSON list")
    return payload


def _parse_date(value: object) -> date | None:
    if value is None or value == "":
        return None
    return date.fromisoformat(str(value))


def _money(value: object) -> Decimal:
    return Decimal(str(value))


def _upsert_users(session: Session, rows: list[dict[str, object]]) -> None:
    for row in rows:
        email = normalize_email(str(row["email"]))
        password_hash = hash_password(str(row["password"]))
        role = UserRole(str(row["role"]))
        name = str(row.get("name") or "")
        user = session.exec(select(User).where(User.email == email)).first()
        if user is None:
            session.add(User(email=email, name=name, password_hash=password_hash, role=role))
            continue
        user.name = name
        user.password_hash = password_hash
        user.role = role
        user.invite_token_hash = None
        user.invite_expires_at = None
        session.add(user)


def _upsert_admin(session: Session) -> None:
    settings = get_settings()
    email = settings.bootstrap_admin_email.strip()
    password = settings.bootstrap_admin_password
    if not email or not password:
        raise SystemExit("BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD are required to load")
    normalized = normalize_email(email)
    user = session.exec(select(User).where(User.email == normalized)).first()
    password_hash = hash_password(password)
    if user is None:
        session.add(
            User(email=normalized, name="Admin", password_hash=password_hash, role=UserRole.admin)
        )
    else:
        user.password_hash = password_hash
        user.role = UserRole.admin
        session.add(user)


def load_json() -> None:
    clients = _load_json("clients.json")
    warehouses = _load_json("warehouses.json")
    carriers = _load_json("carriers.json")
    products = _load_json("products.json")
    orders = _load_json("orders.json")
    users = _load_json("users.json")
    with Session(engine) as session:
        for row in clients:
            session.merge(Client(client_id=str(row["client_id"])))
        for row in warehouses:
            session.merge(
                Warehouse(
                    code=str(row["code"]),
                    region=str(row["region"]),
                    origin_city=str(row["origin_city"]),
                )
            )
        for row in carriers:
            session.merge(Carrier(name=str(row["name"])))
        for row in products:
            session.merge(Product(sku=str(row["sku"]), category=str(row["category"])))
        session.commit()
        for row in orders:
            session.merge(
                Order(
                    order_id=str(row["order_id"]),
                    client_id=str(row["client_id"]),
                    warehouse_code=str(row["warehouse_code"]),
                    carrier_name=str(row["carrier_name"]),
                    sku=str(row["sku"]),
                    destination_city=str(row["destination_city"]),
                    status=OrderStatus(str(row["status"])),
                    order_date=date.fromisoformat(str(row["order_date"])),
                    delivery_date=_parse_date(row["delivery_date"]),
                    quantity=int(str(row["quantity"])),
                    unit_price_usd=_money(row["unit_price_usd"]),
                    order_value_usd=_money(row["order_value_usd"]),
                    is_promo=bool(row["is_promo"]),
                    promo_discount_pct=int(str(row["promo_discount_pct"])),
                )
            )
        _upsert_users(session, users)
        _upsert_admin(session)
        session.commit()


def main(argv: Iterable[str]) -> None:
    args = list(argv)
    if len(args) != 1 or args[0] not in {"export", "load"}:
        raise SystemExit("usage: python scripts/bootstrap/run.py export|load")
    if args[0] == "export":
        export_json()
        return
    load_json()


if __name__ == "__main__":
    main(sys.argv[1:])
