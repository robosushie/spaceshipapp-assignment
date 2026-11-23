"""Pull question jobs from Redis, run the graph, and push the reply."""

from __future__ import annotations

import logging
import time

from redis import Redis
from redis.exceptions import RedisError
from sqlmodel import Session

from src.agent.answer import run_question
from src.agent.queue import BLOCK_SECONDS, SOCKET_GRACE_SECONDS, publish_reply, take_job
from src.lib.config import get_settings
from src.lib.db import engine

logger = logging.getLogger("spaceship.agent")


def build_reply(question: str) -> dict[str, object]:
    with Session(engine) as session:
        return run_question(session, question).model_dump()


def serve(client: Redis) -> None:
    logger.info("agent waiting for questions")
    while True:
        try:
            job = take_job(client)
        except RedisError:
            logger.exception("agent could not read the queue")
            time.sleep(2)
            continue
        if job is None:
            continue
        try:
            reply = build_reply(job["question"])
        except Exception:
            logger.exception("agent job failed")
            reply = {"error": "unavailable"}
        try:
            publish_reply(client, job["id"], reply)
        except RedisError:
            logger.exception("agent could not publish the reply")


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    redis_url = get_settings().redis_url.strip()
    if not redis_url:
        raise SystemExit("REDIS_URL is required")
    client = Redis.from_url(
        redis_url,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=BLOCK_SECONDS + SOCKET_GRACE_SECONDS,
    )
    serve(client)


if __name__ == "__main__":
    main()
