from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from src.services.titles import chat_title


def test_chat_titles_require_a_token(client: TestClient) -> None:
    response = client.post("/v1/chat-titles", json={"message": "Plot delivered orders by week"})
    assert response.status_code == 401


def test_missing_openai_key_keeps_the_message(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.services.titles.get_settings",
        lambda: type("Settings", (), {"openai_api_key": ""})(),
    )
    assert chat_title("Plot delivered orders by week") == "Plot delivered orders by week"


def test_chat_title_uses_the_model_text(monkeypatch: MonkeyPatch) -> None:
    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {"choices": [{"message": {"content": "Weekly deliveries"}}]}

    def post(*_args: object, **kwargs: object) -> Response:
        body = kwargs["json"]
        assert isinstance(body, dict)
        assert body["model"] == "gpt-5-nano"
        assert body["messages"][1]["content"] == "Plot delivered orders by week"
        return Response()

    monkeypatch.setattr(
        "src.services.titles.get_settings",
        lambda: type("Settings", (), {"openai_api_key": "test-key"})(),
    )
    monkeypatch.setattr("src.services.titles.httpx.post", post)
    assert chat_title("Plot delivered orders by week") == "Weekly deliveries"
