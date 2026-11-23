"""Redis list used as the question queue between the API and the agent."""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

JOBS = "questions"
REPLY_TTL_SECONDS = 180
WAIT_SECONDS = 170
BLOCK_SECONDS = 5
SOCKET_GRACE_SECONDS = 10


def reply_key(job_id: str) -> str:
    return f"reply:{job_id}"


def enqueue(client: Any, question: str) -> str:
    job_id = uuid4().hex
    client.lpush(JOBS, json.dumps({"id": job_id, "question": question}))
    return job_id


def wait_for_reply(
    client: Any,
    job_id: str,
    timeout: int = WAIT_SECONDS,
) -> dict[str, object] | None:
    popped = client.blpop(reply_key(job_id), timeout=timeout)
    if popped is None:
        return None
    return json.loads(popped[1])


def take_job(client: Any, timeout: int = BLOCK_SECONDS) -> dict[str, str] | None:
    popped = client.brpop(JOBS, timeout=timeout)
    if popped is None:
        return None
    payload = json.loads(popped[1])
    if not isinstance(payload, dict):
        return None
    job_id = payload.get("id")
    question = payload.get("question")
    if not isinstance(job_id, str) or not isinstance(question, str):
        return None
    return {"id": job_id, "question": question}


def publish_reply(client: Any, job_id: str, body: dict[str, object]) -> None:
    key = reply_key(job_id)
    client.lpush(key, json.dumps(body))
    client.expire(key, REPLY_TTL_SECONDS)
