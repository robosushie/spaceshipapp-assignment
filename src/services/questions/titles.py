import logging

import httpx

from src.lib.config import get_settings

logger = logging.getLogger("spaceship.titles")
_MODEL = "gpt-5-nano"
_URL = "https://api.openai.com/v1/chat/completions"


def chat_title(message: str) -> str:
    key = get_settings().openai_api_key.strip()
    if not key:
        return message
    try:
        response = httpx.post(
            _URL,
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": _MODEL,
                "reasoning_effort": "minimal",
                "max_completion_tokens": 256,
                "messages": [
                    {
                        "role": "developer",
                        "content": (
                            "Write a tab label of two to five words for the user message. "
                            "Paraphrase it. Do not copy the message. No punctuation."
                        ),
                    },
                    {"role": "user", "content": message},
                ],
            },
            timeout=20,
        )
        response.raise_for_status()
        title = _clean(_content(response.json()), message)
    except httpx.HTTPError, ValueError, KeyError, TypeError:
        logger.exception("chat title failed")
        return message
    return title


def _content(body: object) -> str:
    if not isinstance(body, dict):
        return ""
    choices = body.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            item["text"]
            for item in content
            if isinstance(item, dict) and isinstance(item.get("text"), str)
        ]
        return " ".join(parts)
    return ""


def _clean(title: str, fallback: str) -> str:
    line = title.strip().splitlines()[0].strip(" \"'`") if title.strip() else ""
    line = line.rstrip(".")
    if not line:
        return fallback
    return line[:80]
