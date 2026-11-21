---
name: folder-structure
description: "Places app code in the folders named by choices.layout. Use on every project created with brix init."
---

# Folder structure

This skill is installed on every stack. Read `stack.json` `choices.layout` and apply that layout. Ignore every other layout in this file.

When `choices.layout` is missing, use this suggestion:

- A JavaScript UI plus Hono, Express, or Fastify, and `turbo` is `turborepo`: `apps-packages`.
- A JavaScript UI plus Hono, Express, or Fastify: `packages`.
- A JavaScript UI plus FastAPI, Flask, or Django: `apps-src`.
- Next.js with no separate API: `next-app`.
- Frontend only, or backend only: `single-src`.
- None of the matches above: `split`.
- A JavaScript API grouped by feature, rather than by routes and services: `feature-modules`. This does not replace an earlier match.

Use generic folder names: `src`, `app`, `components`, `hooks`, `lib`, `services`, `models`, `schemas`, `types`, `styles`, `routes`, `pages`, `docs`, `public`, `scripts`. Do not create a top-level folder named after a product feature or a sample app. Feature URLs live inside `app/`, `pages/`, or `routes/`.

Shared rules:

- `docs/` is for human notes. `scripts/bootstrap/` is for seed data and one-off setup.
- `public/` is static files for a web app. It stays at that app's root.
- `types/` (TypeScript) or `schemas/` (Python) holds shapes that cross a boundary. Database tables stay in `models/` or the ORM folder.
- `src/agent/` exists only when an AI framework is selected. It holds that framework's library: prompts, tools, graphs, crews, and generated clients.
- `services/` owns use cases. Each file is a runner: it calls `src/agent/` (or `src/mastra/`) and returns a result. It does not define tools, prompts, crews, or graphs.
- Tests sit beside the project root (`tests/` for Python, the test runner's folder for TypeScript), not inside route files' feature folders.
- A second UI folder exists only when there is a second UI. A worker folder exists only when there is a worker.
- Create the UI root only when a frontend is selected. Create the API root only when a backend is selected.

## UI apps, API at root

`choices.layout` is `apps-src`. JavaScript UIs live under `apps/`. The API stays at the repo root. Do not create an npm package for the API.

```
apps/web/                      frontend interior
apps/admin/                    only when there is a second UI
src/                           the API, except Django
infra/                         only when Docker, Helm, or Postgres Docker is selected
```

The frontend interior goes in `apps/web` (and `apps/admin` for a second UI).

Vite, React, or SvelteKit:

```
src/components/ui/
src/components/layout/
src/components/shared/
src/hooks/
src/lib/
src/pages/                or src/routes/ when the router uses routes
src/styles/
src/types/
src/assets/
public/
```

SvelteKit keeps the `src/routes` tree its CLI emits. Do not add a parallel `pages/` tree.

FastAPI or Flask. `pyproject.toml` stays at the repo root. The Python project is not an npm workspace member.

```
src/api/routes/
src/agent/                     framework library, only when an AI framework is selected
src/services/                  runners that call src/agent/; no prompts, tools, or graphs
src/models/
src/schemas/
src/lib/
src/constants/
src/enums/
alembic/                       only when the ORM is SQLAlchemy
tests/
docs/
scripts/bootstrap/
pyproject.toml
```

## Infra

Create `infra/` only when Docker, Kubernetes + Helm, or Postgres Docker is selected. Do not put a Dockerfile, compose file, or chart inside `src/`.

```
infra/compose/docker-compose.yml
infra/docker/
infra/helm/<service>/
  Chart.yaml
  values.yaml
  templates/
```

`<service>` is a role (`api`, `web`, `worker`), not a product name. Helm templates use dashed file names.
