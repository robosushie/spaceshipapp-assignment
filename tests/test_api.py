from datetime import date

from fastapi.testclient import TestClient

from tests.helpers import add_order, add_user


def test_health_is_only_status(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    body = response.text.lower()
    assert "postgres" not in body
    assert "traceback" not in body
    assert "version" not in body


def test_login_hides_whether_the_email_exists(client: TestClient) -> None:
    add_user()
    unknown = client.post(
        "/v1/auth/login",
        json={"email": "missing@spaceship.local", "password": "nope"},
    )
    wrong = client.post(
        "/v1/auth/login",
        json={"email": "analyst@spaceship.local", "password": "wrong"},
    )
    assert unknown.status_code == 401
    assert wrong.status_code == 401
    assert unknown.json() == wrong.json()
    assert unknown.headers["content-type"].startswith("application/problem+json")
    assert unknown.json()["detail"] == "Email or password is incorrect."


def test_orders_require_a_token(client: TestClient) -> None:
    response = client.get("/v1/orders")
    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/problem+json")


def _token(client: TestClient) -> str:
    add_user()
    response = client.post(
        "/v1/auth/login",
        json={"email": "analyst@spaceship.local", "password": "correct-password"},
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


def test_orders_returns_a_page(client: TestClient) -> None:
    add_order()
    token = _token(client)
    response = client.get("/v1/orders", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["offset"] == 0
    assert body["items"][0]["order_id"] == "ORD-1"
    assert body["items"][0]["region"] == "UK"
    assert body["items"][0]["order_value_usd"] == "26.22"


def test_column_filter_narrows_the_page(client: TestClient) -> None:
    add_order()
    token = _token(client)
    headers = {"Authorization": f"Bearer {token}"}
    hit = client.get(
        "/v1/orders",
        params={"filter": "destination_city:contains:Leeds"},
        headers=headers,
    )
    miss = client.get(
        "/v1/orders",
        params={"filter": "destination_city:contains:Nowhere"},
        headers=headers,
    )
    rejected = client.get("/v1/orders", params={"filter": "drop:equals:x"}, headers=headers)
    assert hit.status_code == 200
    assert hit.json()["total"] == 1
    assert miss.json()["total"] == 0
    assert rejected.status_code == 422


def test_limit_above_max_is_422(client: TestClient) -> None:
    token = _token(client)
    response = client.get(
        "/v1/orders",
        params={"limit": 51},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["status"] == 422
    assert any(error["pointer"] == "/limit" for error in body["errors"])


def test_missing_order_is_404(client: TestClient) -> None:
    token = _token(client)
    response = client.get("/v1/orders/missing", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


def test_metrics_counts_december_deliveries(client: TestClient) -> None:
    add_order("ORD-OCT", date(2025, 10, 19))
    add_order("ORD-DEC", date(2025, 12, 15))
    token = _token(client)
    response = client.get("/v1/metrics", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["deliveries_last_month"] == 1
    assert body["carriers"] == 1
    assert body["warehouses"] == 1
    assert body["clients"] == 1
    assert body["products"] == 1
    assert body["totals"]["orders"] == 2
    assert body["totals"]["delivered"] == 2
    assert body["totals"]["on_time_rate"] == "1.0000"
    assert body["totals"]["average_delivery_days"] == "0.0"
    assert body["by_month"] == [
        {"month": "2025-10", "orders": 1},
        {"month": "2025-12", "orders": 1},
    ]


def test_questions_without_a_key_are_unavailable(client: TestClient) -> None:
    token = _token(client)
    response = client.post(
        "/v1/questions",
        json={"question": "How many orders were delayed?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 503
    assert response.json()["status"] == 503
