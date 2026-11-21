# Next steps

## Checks

- `uv run ruff check` — pass
- `uv run ruff format --check` — pass
- `uv run mypy` — pass
- `uv run pytest` — pass (health, identical login 401s, orders 401, orders 200, limit 51 → 422, missing order 404, questions 503)
- `pnpm --filter web typecheck` — pass
- `pnpm --filter web test` — pass
- Postgres compose on port 54329 — up, migrated, 400 orders seeded
- Desk in the browser — sign-in, status counts, next page, delayed filter (55 orders), ask without an Anthropic key (503 message)

Playwright (`pnpm --filter web test:e2e`) is not in CI. Run it locally with `pnpm dev` already up and the bootstrap admin variables exported.

## You still fill in

- `ANTHROPIC_API_KEY` in `.env` before Ask can call the model
- A new `JWT_SECRET` if this `.env` is copied anywhere besides this machine
- `COOKIE_SECURE=true` when the API is served over HTTPS

## Local run

From the repo root: `pnpm install`, `uv sync`, `pnpm db:create`, `pnpm db:migrate`, `pnpm db:seed`, `pnpm dev`. Sign in with `BOOTSTRAP_ADMIN_EMAIL` and `BOOTSTRAP_ADMIN_PASSWORD` from `.env`. If port 5173 is already taken, Vite prints the port it chose.
