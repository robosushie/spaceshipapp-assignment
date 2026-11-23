import logging
import re

from fastapi.testclient import TestClient
from pytest import LogCaptureFixture, MonkeyPatch

from src.lib.config import get_settings
from tests.helpers import add_user


def test_unknown_email_does_not_send_a_reset(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    add_user()
    settings = get_settings()
    monkeypatch.setattr(settings, "resend_api_key", "re_test_key_not_real")
    called = False

    def send(_payload: object) -> dict[str, str]:
        nonlocal called
        called = True
        return {"id": "email_1"}

    monkeypatch.setattr("src.services.identity.mail.resend.Emails.send", send)
    missing = client.post("/v1/auth/forgot", json={"email": "missing@example.com"})
    other = client.post("/v1/auth/forgot", json={"email": "other@example.com"})
    assert missing.status_code == 204
    assert other.status_code == 204
    assert missing.content == other.content == b""
    assert called is False


def test_reset_mail_sets_a_usable_password(
    client: TestClient,
    monkeypatch: MonkeyPatch,
    caplog: LogCaptureFixture,
) -> None:
    add_user()
    settings = get_settings()
    monkeypatch.setattr(settings, "resend_api_key", "re_test_key_not_real")
    monkeypatch.setattr(settings, "web_origin", "http://localhost:5174")
    sent: dict[str, object] = {}

    def send(payload: dict[str, object]) -> dict[str, str]:
        sent.update(payload)
        return {"id": "email_1"}

    monkeypatch.setattr("src.services.identity.mail.resend.Emails.send", send)
    with caplog.at_level(logging.DEBUG):
        response = client.post("/v1/auth/forgot", json={"email": "analyst@spaceship.local"})
    assert response.status_code == 204
    assert "re_test_key_not_real" not in response.text
    assert "re_test_key_not_real" not in caplog.text
    match = re.search(r"token=([^\"&]+)", str(sent["html"]))
    assert match is not None
    raw = match.group(1)
    assert raw not in response.text
    accepted = client.post("/v1/auth/reset", json={"token": raw, "password": "a-new-password"})
    assert accepted.status_code == 204
    login = client.post(
        "/v1/auth/login",
        json={"email": "analyst@spaceship.local", "password": "a-new-password"},
    )
    assert login.status_code == 200
