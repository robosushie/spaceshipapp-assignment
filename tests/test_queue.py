import json
from typing import cast

import pytest
from fastapi import HTTPException
from sqlmodel import Session

from src.agent.answer import run_question
from src.agent.queue import JOBS, enqueue, publish_reply, take_job, wait_for_reply
from src.agent.worker import build_reply
from src.services.questions.questions import ask_question


class MemoryRedis:
    def __init__(self) -> None:
        self.lists: dict[str, list[str]] = {}
        self.expirations: dict[str, int] = {}

    def lpush(self, key: str, value: str) -> int:
        bucket = self.lists.setdefault(key, [])
        bucket.insert(0, value)
        return len(bucket)

    def blpop(self, keys: str, timeout: int = 0) -> tuple[str, str] | None:
        bucket = self.lists.get(keys) or []
        if not bucket:
            return None
        return keys, bucket.pop(0)

    def brpop(self, keys: str, timeout: int = 0) -> tuple[str, str] | None:
        bucket = self.lists.get(keys) or []
        if not bucket:
            return None
        return keys, bucket.pop()

    def expire(self, key: str, seconds: int) -> bool:
        self.expirations[key] = seconds
        return True


def test_enqueue_waits_for_the_reply() -> None:
    client = MemoryRedis()
    job_id = enqueue(client, "how many orders")
    job = take_job(client)
    assert job is not None
    assert job["id"] == job_id
    assert job["question"] == "how many orders"
    publish_reply(client, job_id, {"answer": "400", "plot_required": False})
    assert wait_for_reply(client, job_id, timeout=1) == {
        "answer": "400",
        "plot_required": False,
    }
    assert client.expirations


def test_run_question_returns_the_graph_answer(monkeypatch: pytest.MonkeyPatch) -> None:
    from langchain_core.messages import AIMessage, HumanMessage

    session = cast(Session, object())

    def invoke(state: dict[str, object], config: dict[str, object]) -> dict[str, object]:
        messages = state["messages"]
        assert isinstance(messages, list)
        assert isinstance(messages[0], HumanMessage)
        assert messages[0].content == "how many"
        configurable = config["configurable"]
        assert isinstance(configurable, dict)
        assert configurable["session"] is session
        return {"messages": [messages[0], AIMessage(content="400 orders")]}

    monkeypatch.setattr("src.agent.answer.graph.invoke", invoke)
    response = run_question(session, "how many")
    assert response.answer == "400 orders"
    assert response.chart is None
    assert response.plot_required is False


def test_worker_builds_the_graph_answer(monkeypatch: pytest.MonkeyPatch) -> None:
    from langchain_core.messages import AIMessage, HumanMessage

    class Opened:
        def __enter__(self) -> object:
            return object()

        def __exit__(self, *_args: object) -> None:
            return None

    monkeypatch.setattr("src.agent.worker.Session", lambda _engine: Opened())

    def invoke(state: dict[str, object], config: dict[str, object]) -> dict[str, object]:
        messages = state["messages"]
        assert isinstance(messages, list)
        assert isinstance(messages[0], HumanMessage)
        assert messages[0].content == "how many"
        return {"messages": [messages[0], AIMessage(content="400 orders")]}

    monkeypatch.setattr("src.agent.answer.graph.invoke", invoke)
    assert build_reply("how many")["answer"] == "400 orders"


def test_ask_without_redis_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    class Settings:
        anthropic_api_key = "sk-test"
        redis_url = ""

    monkeypatch.setattr(
        "src.services.questions.questions.get_settings",
        lambda: Settings(),
    )
    with pytest.raises(HTTPException) as caught:
        ask_question("how many")
    assert caught.value.status_code == 503


def test_ask_question_returns_the_queued_reply(monkeypatch: pytest.MonkeyPatch) -> None:
    client = MemoryRedis()
    push = client.lpush

    def lpush(key: str, value: str) -> int:
        count = push(key, value)
        if key == JOBS:
            job = json.loads(value)
            publish_reply(client, str(job["id"]), {"answer": "400", "plot_required": False})
        return count

    client.lpush = lpush  # type: ignore[method-assign]

    class Settings:
        anthropic_api_key = "sk-test"
        redis_url = "redis://localhost:6379/0"

    monkeypatch.setattr(
        "src.services.questions.questions.get_settings",
        lambda: Settings(),
    )
    monkeypatch.setattr(
        "src.services.questions.questions.Redis.from_url",
        lambda *args, **kwargs: client,
    )
    response = ask_question("how many")
    assert response.answer == "400"
    assert response.plot_required is False
