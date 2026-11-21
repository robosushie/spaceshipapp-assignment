---
name: sqlalchemy
description: "Adds SQLAlchemy for a Python API. Use when stack.json orm is sqlalchemy."
---

# SQLAlchemy

Use SQLAlchemy 2.x style only.

## Files

```
src/lib/db.py           create_engine / create_async_engine + sessionmaker / async_sessionmaker, and Base(DeclarativeBase)
src/models/            Mapped[...] + mapped_column; import all models so metadata sees them
src/api/deps.py        yield a session per request, then close / context-manage it
alembic.ini                at the Python project root
alembic/env.py
alembic/versions/
```

## Models and sessions (official 2.0)

- Models use `Mapped` and `mapped_column` on `DeclarativeBase`. Do not use the legacy declarative `Column` style on a declarative base.
- Sync: `sessionmaker(bind=engine)`. Async: `async_sessionmaker(engine, expire_on_commit=False)` and `create_async_engine` with an async driver (`asyncpg`, etc.).
- Set `expire_on_commit=False` for asyncio so committed attributes stay readable without implicit IO (avoids `MissingGreenlet`). Prefer `selectinload` / eager options over lazy IO in async code.
- One engine per process. Routes never call `create_engine` or open ad hoc sessions — only `Depends` / Flask teardown.

## Alembic

Alembic is the migration tool for this ORM. From the Python project root: `alembic init` (async template when the engine is async). `env.py` sets `target_metadata = Base.metadata` and imports model modules so autogenerate sees them. Script location stays `alembic/` next to `alembic.ini`, not inside `src/`. Apply with `alembic upgrade head`.

## Database URL

Read `DATABASE_URL` from the env schema. That URL is the only connection setting the app uses. Do not hard-code it. The URL matches the provider in `stack.json` (Neon, Supabase, Railway, Render, RDS, local Docker, or another host).

## Pooler and direct URLs

When the provider offers a pooler and a direct URL, use the pooler for runtime app traffic and the direct URL for migrations (Drizzle Kit, Prisma migrate, Alembic). Migrations need a session connection for DDL. Do not point the migration tool at a transaction pooler.

## One migration path

One database, one migration path. The ORM skill owns migrations (Alembic, Drizzle, Prisma, or Django). Do not add a second system. Do not ship schema changes with `metadata.create_all` alone when a migration tool is selected.
