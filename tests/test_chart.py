from datetime import date

from sqlmodel import Session

from src.agent.sql_guard import run_select
from src.lib.db import engine
from tests.helpers import add_order

_WEEKLY = """
SELECT to_char(date_trunc('week', order_date), 'YYYY-MM-DD') AS week,
       count(*) AS orders
FROM orders
WHERE status = 'delivered'
  AND order_date >= DATE '2025-10-01'
  AND order_date <= DATE '2025-12-30'
GROUP BY 1
ORDER BY 1
"""


def test_weekly_select_keeps_in_range_orders() -> None:
    add_order("ORD-IN-1", date(2025, 10, 6))
    add_order("ORD-IN-2", date(2025, 10, 20))
    add_order("ORD-OUT", date(2025, 9, 15))
    with Session(engine) as session:
        rows = run_select(session, _WEEKLY)

    counts = {row["week"]: row["orders"] for row in rows}
    assert counts["2025-10-06"] == "1"
    assert counts["2025-10-20"] == "1"
    assert "2025-09-15" not in counts
