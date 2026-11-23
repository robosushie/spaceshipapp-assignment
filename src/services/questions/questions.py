import logging

from fastapi import HTTPException
from redis import Redis
from redis.exceptions import RedisError

from src.agent.queue import SOCKET_GRACE_SECONDS, WAIT_SECONDS, enqueue, wait_for_reply
from src.lib.config import get_settings
from src.schemas.questions.question import QuestionResponse

logger = logging.getLogger("spaceship.questions")
_UNAVAILABLE = "Questions are unavailable."


def ask_question(question: str) -> QuestionResponse:
    settings = get_settings()
    if not settings.anthropic_api_key.strip() or not settings.redis_url.strip():
        raise HTTPException(status_code=503, detail=_UNAVAILABLE)
    try:
        client = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=WAIT_SECONDS + SOCKET_GRACE_SECONDS,
        )
        job_id = enqueue(client, question)
        reply = wait_for_reply(client, job_id, timeout=WAIT_SECONDS)
    except RedisError:
        logger.exception("question queue failed")
        raise HTTPException(status_code=503, detail=_UNAVAILABLE) from None
    if not isinstance(reply, dict) or "error" in reply:
        raise HTTPException(status_code=503, detail=_UNAVAILABLE)
    return QuestionResponse.model_validate(reply)
