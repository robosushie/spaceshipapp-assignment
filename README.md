# Spaceship

Internal desk for the 2025 shipping book: 400 stationery orders, nine carriers, nine warehouses. The design notes are in [docs/architecture.md](docs/architecture.md), [docs/api.md](docs/api.md), [docs/design.md](docs/design.md), and [docs/auth.md](docs/auth.md).

## Run locally

```bash
pnpm install
uv sync
cp .env.example .env
```

Put a `JWT_SECRET` of at least 32 bytes in `.env`. Postgres is published on port **54329** so it does not collide with anything already listening on 5432.

```bash
pnpm db:create
pnpm db:migrate
pnpm db:seed
pnpm dev
```

- Desk: http://localhost:5173
- API: http://127.0.0.1:8000
- OpenAPI: http://127.0.0.1:8000/docs

`pnpm db:seed` loads the desk users from `scripts/bootstrap/data/users.json`. Sign in as `admin@spaceship.test` or `member@spaceship.test` with password `spaceship_1234`. The access token stays in memory. A reload uses the refresh cookie.

`POST /v1/questions` returns 503 until `ANTHROPIC_API_KEY` is set. The rest of the desk works without it.

## Deploy

Actions → **deploy** → **Run workflow**, then choose the branch in **Use workflow from**. That run creates Postgres, the API, and the web service if they are missing, then uploads the API and web images from the selected branch. `ci` does not deploy.

The API pre-deploy command applies pending Alembic revisions, then loads the shipping book only when `orders` is empty. A database that already has orders is left as it is.

The Railway project must be named `spaceship`. Repository secrets `RAILWAY_TOKEN` and `JWT_SECRET` are required. `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `RESEND_API_KEY`, and `RESEND_FROM` are optional.

## Scripts

| Script | What it does |
| --- | --- |
| `pnpm dev` | API and Vite together, via concurrently |
| `pnpm db:create` | Start Postgres from `infra/compose/docker-compose.yml` |
| `pnpm db:make -- "message"` | Alembic autogenerate |
| `pnpm db:migrate` | `alembic upgrade head` |
| `pnpm db:seed` | Load `scripts/bootstrap/data/*.json`, including the desk users |
| `pnpm db:export` | Rebuild those JSON files from `docs/manuals/mock_logistics_data.csv` |

Python checks: `uv run ruff check`, `uv run ruff format --check`, `uv run mypy`, `uv run pytest`.

Web checks: `pnpm --filter web typecheck` and `pnpm --filter web test`. A Playwright spec lives in `apps/web/e2e` and is meant to be run locally with `pnpm --filter web test:e2e` while `pnpm dev` is up.
