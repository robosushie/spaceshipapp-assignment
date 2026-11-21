---
name: postgres
description: "Adds Postgres for local and hosted use. Use when stack.json database is postgres."
---

# Postgres

Use Postgres as the database named in `stack.json`.

## Database URL

Read `DATABASE_URL` from the env schema. That URL is the only connection setting the app uses. Do not hard-code it. The URL matches the provider in `stack.json` (Neon, Supabase, Railway, Render, RDS, local Docker, or another host).

## Pooler and direct URLs

When the provider offers a pooler and a direct URL, use the pooler for runtime app traffic and the direct URL for migrations (Drizzle Kit, Prisma migrate, Alembic). Migrations need a session connection for DDL. Do not point the migration tool at a transaction pooler.

## Local Docker (`dbProvider.postgres-docker`)

Service definition lives in `infra/compose/docker-compose.yml`:

- Official `postgres` image with a pinned major tag.
- Named volume for data.
- Ports published only for local use.
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` from a gitignored env file; mirror the keys in `.env.example`.
- App `DATABASE_URL` points at that service name from Compose networks, or `localhost` when the API runs on the host.

## Hosted (Neon, Supabase, Railway, Render, AWS RDS)

Do not start a local Postgres container.

## TLS

Use TLS / `sslmode` as the provider requires. Do not disable certificate verification to make a connection succeed.

## One migration path

One database, one migration path. The ORM skill owns migrations (Alembic, Drizzle, Prisma, or Django). Do not add a second system. Do not ship schema changes with `metadata.create_all` alone when a migration tool is selected.

## Health

`GET /health` returns a small JSON body and does not leak config, versions, stack traces, SQL, or dependency status. Do not expose connection strings. HTTP health stays separate from database liveness unless the product explicitly wants a readiness probe that checks the database.
