from typing import Any

from fastapi.responses import JSONResponse
from pydantic import BaseModel


class FieldError(BaseModel):
    pointer: str
    detail: str


class Problem(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    instance: str | None = None
    errors: list[FieldError] | None = None


_TITLES: dict[int, tuple[str, str]] = {
    400: ("bad-request", "Bad request"),
    401: ("unauthorized", "Unauthorized"),
    403: ("forbidden", "Forbidden"),
    404: ("not-found", "Not found"),
    422: ("validation-error", "Validation failed"),
    429: ("rate-limited", "Too many requests"),
    500: ("internal", "Internal error"),
    503: ("unavailable", "Unavailable"),
}


def problem(
    status: int,
    detail: str,
    instance: str,
    errors: list[FieldError] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    slug, title = _TITLES.get(status, ("error", "Error"))
    body = Problem(
        type=f"https://spaceship.local/problems/{slug}",
        title=title,
        status=status,
        detail=detail,
        instance=instance,
        errors=errors,
    )
    return JSONResponse(
        status_code=status,
        content=body.model_dump(exclude_none=True),
        media_type="application/problem+json",
        headers=headers,
    )


def pointer_from_loc(loc: tuple[Any, ...] | list[Any]) -> str:
    parts = [str(part) for part in loc if part not in {"body", "query", "path"}]
    if not parts:
        return "/"
    return "/" + "/".join(parts)
