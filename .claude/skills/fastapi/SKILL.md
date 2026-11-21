---
name: fastapi
description: "Scaffolds a FastAPI service with uv. Use when stack.json backend is fastapi."
---

# FastAPI

Use `uv` in the API root named by the `folder-structure` skill for `choices.layout`. Prefer `uv init` there, then move the app modules into that root's `src/` tree and `uv add fastapi uvicorn[standard]` (and the ORM / driver packages from the other skills). `pyproject.toml` stays in that root.

## App shape (official bigger-applications + lifespan)

```
src/main.py                 FastAPI(lifespan=...), include_router(...)
src/api/deps.py             Depends() providers (session, current user)
src/api/routes/health.py    APIRouter, GET /health
src/api/routes/<resource>.py
src/lib/config.py           Settings from env
src/schemas/                Pydantic v2 models
src/services/
src/models/                 when an ORM is selected
```

- Create shared resources (engine, pool) once in a lifespan context manager; store on `app.state` if needed. Prefer lifespan over deprecated `on_event("startup")`.
- Hand out per-request resources with `Depends` and `yield` (session closes after the request). Annotate with `Annotated[..., Depends(...)]`.
- Include routers: `app.include_router(health.router)` and `app.include_router(books.router, prefix="/v1")`.
- OpenAPI is automatic at `/docs` / `/openapi.json`; keep response models on the path operations.

Use the ORM named in `stack.json`. Pydantic schemas live in `schemas/`, not on SQLAlchemy models.

## Health

`GET /health` returns a small JSON body and does not leak config, versions, stack traces, SQL, or dependency status. Do not expose connection strings. HTTP health stays separate from database liveness unless the product explicitly wants a readiness probe that checks the database.

## Process boundary

Do not add a Node backend next to this Python service. Do not put the uv project inside an npm workspace.

## Where this framework's files go

Follow the `folder-structure` skill and `stack.json` `choices.layout`. Put this framework's entry, routes, and services in the folders that skill names. Do not invent a second tree, and do not add a top-level folder named after a product feature.
