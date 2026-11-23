import logging
import re

from fastapi.testclient import TestClient
from pytest import LogCaptureFixture, MonkeyPatch

from src.enums import UserRole
from src.lib.config import get_settings
from tests.helpers import add_user


def _token(client: TestClient, email: str = "analyst@spaceship.local") -> str:
    response = client.post(
        "/v1/auth/login",
        json={"email": email, "password": "correct-password"},
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


def test_profile_update(client: TestClient) -> None:
    add_user()
    token = _token(client)
    updated = client.post(
        "/v1/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Ada Lovelace",
            "title": "Ops lead",
            "department": "Logistics",
            "role": "admin",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Ada Lovelace"
    assert updated.json()["title"] == "Ops lead"
    assert updated.json()["department"] == "Logistics"
    assert updated.json()["role"] == "member"
    assert updated.json()["email"] == "analyst@spaceship.local"
    again = client.get("/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert again.json()["role"] == "member"
    assert again.json()["title"] == "Ops lead"


def test_password_rejects_the_current_password(client: TestClient) -> None:
    add_user()
    token = _token(client)
    rejected = client.post(
        "/v1/me/password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "nope", "new_password": "a-new-password"},
    )
    assert rejected.status_code == 401
    assert rejected.json()["detail"] == "Email or password is incorrect."
    login = client.post(
        "/v1/auth/login",
        json={"email": "analyst@spaceship.local", "password": "correct-password"},
    )
    assert login.status_code == 200


def test_member_cannot_invite(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    add_user()
    called = False

    def send(_payload: object) -> dict[str, str]:
        nonlocal called
        called = True
        return {"id": "email_1"}

    monkeypatch.setattr("src.services.mail.resend.Emails.send", send)
    token = _token(client)
    response = client.post(
        "/v1/invites",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Grace", "email": "grace@example.com", "role": "member"},
    )
    assert response.status_code == 403
    assert called is False


def test_invite_sends_mail_without_logging_the_key(
    client: TestClient,
    monkeypatch: MonkeyPatch,
    caplog: LogCaptureFixture,
) -> None:
    add_user(email="admin@spaceship.local", role=UserRole.admin, name="Ada")
    settings = get_settings()
    monkeypatch.setattr(settings, "resend_api_key", "re_test_key_not_real")
    monkeypatch.setattr(settings, "web_origin", "http://localhost:5174")
    sent: dict[str, object] = {}

    def send(payload: dict[str, object]) -> dict[str, str]:
        sent.update(payload)
        return {"id": "email_1"}

    monkeypatch.setattr("src.services.mail.resend.Emails.send", send)
    token = _token(client, "admin@spaceship.local")
    with caplog.at_level(logging.DEBUG):
        response = client.post(
            "/v1/invites",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Grace", "email": "Grace@Example.com", "role": "member"},
        )
    assert response.status_code == 201
    assert response.json() == {"email": "grace@example.com"}
    assert "re_test_key_not_real" not in response.text
    assert "re_test_key_not_real" not in caplog.text
    html = str(sent["html"])
    match = re.search(r"token=([^\"&]+)", html)
    assert match is not None
    raw = match.group(1)
    assert raw not in response.text
    accepted = client.post(
        "/v1/invites/accept",
        json={"token": raw, "password": "a-new-password"},
    )
    assert accepted.status_code == 204
    login = client.post(
        "/v1/auth/login",
        json={"email": "grace@example.com", "password": "a-new-password"},
    )
    assert login.status_code == 200
