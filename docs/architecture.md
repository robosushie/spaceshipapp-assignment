# Architecture

Spaceship is an internal logistics desk for one shipping book. The book is the 400-row file at `docs/manuals/mock_logistics_data.csv`: stationery orders (crayons, paper, paint, and the rest) moved by nine carriers out of nine warehouses between 1 Jan 2025 and 30 Dec 2025.

This document is why the stack is shaped the way it is. The HTTP contract is in [api.md](api.md). Sign-in is in [auth.md](auth.md). How to use the desk is in [using.md](using.md). The screen is in [design.md](design.md).

## What the book actually is

| Fact | Value |
| --- | --- |
| Orders | 400, one row per `order_id` |
| Clients | 30, identified only by `client_id` |
| Warehouses | 9, each with one region and one origin city |
| Carriers | 9 |
| SKUs | 355, each with one category |
| Categories | 8 |
| Regions | UK, EU, US-E, US-C, US-W |
| Status | 304 delivered, 55 delayed, 27 in transit, 11 exception, 3 canceled |
| Missing delivery date | 30 rows, exactly the in-transit and canceled orders |
| Money | `order_value_usd` always equals `quantity * unit_price_usd`. Promo percent is recorded and is not applied to the value. |

The desk reads this book. It does not take new orders, talk to carriers, or bill anyone.

## Why this stack

The repo is a Brix `apps-src` project: the Vite app lives in `apps/web`, the FastAPI service lives at the repo root under `src/`, and the Python project is not a pnpm workspace member. `stack.json` names SQLAlchemy as the ORM. Tables are SQLModel classes, which are SQLAlchemy 2 models that also validate like Pydantic. Alembic still owns the schema. Request and response bodies stay in `src/schemas/` so a table change does not silently become an API change.

| Piece | Role on this desk |
| --- | --- |
| FastAPI | HTTP, OpenAPI, dependency injection. Routes validate, call one service, and return. |
| Pydantic v2 / SQLModel | Settings, HTTP bodies, and table rows. |
| Postgres in Docker | The only database. Local, one named volume, credentials from `.env`. |
| Alembic | The only migration path. The app does not call `create_all`. |
| Ruff | Format and lint for the Python tree. |
| mypy | Typecheck for `src/` and `scripts/`. Migrations are excluded. |
| LangGraph | The steps of a question: write SQL, check and run it, explain the rows, with two repairs. |
| BAML (Boundary) | The structured calls to Anthropic. The model returns one SELECT plus whether a plot is required, then a paragraph. |
| Vite + React + TypeScript | The desk UI. |
| Tailwind + shadcn | Components and tokens. Charts go through the shadcn Chart wrapper around Recharts. |
| pnpm + concurrently | `pnpm dev` starts the API and the web app together. |

Sync SQLAlchemy is deliberate. The book is 400 rows. The seed script, Alembic, and the request path all use one session style. Async can replace the engine later without a schema change.

`ANTHROPIC_API_KEY` is optional at process start. The desk, the table, and the charts work with an empty key. `POST /v1/questions` returns 503 until the key is set. `JWT_SECRET` and `DATABASE_URL` are required at start.

## Request path

```
apps/web  --proxy /v1 and /health-->  src/api/routes
                                         |
                                         v
                                    src/services
                                    /          \
                          SQLModel session    src/agent  (questions only)
                                                 |
                                            BAML functions
                                                 |
                                              Anthropic
```

Rules that keep the path honest:

- A route does not run a query and does not import BAML or LangGraph.
- A service owns one use case. It does not read `Request` except where auth already turned the caller into a user.
- `src/agent/` holds the graph, the nodes, the schema prompt, the SQL guard, and the generated BAML client. Model SQL is parsed and allow-listed before it runs. It is one read-only SELECT on the shipping book.
- `src/services/questions.py` is the only module that invokes the compiled graph.
- Settings are read once in `src/lib/config.py`. Route handlers do not touch `os.environ`.

## Schema

Natural keys from the file are the primary keys. Nothing in the book is a surrogate id.

- `clients.client_id`
- `warehouses.code`, plus `region` and `origin_city` (both constant per warehouse)
- `carriers.name`
- `products.sku`, plus `category`
- `orders.order_id`, foreign keys to those four, plus destination city, status, dates, quantity, unit price, order value, promo flag, promo percent
- `users` — email, name, argon2 password hash, role `member` or `admin`, optional invite token hash and expiry
- `refresh_tokens` — sha256 hash of the token, expiry, `revoked_at`, user id

`orders.region` is not stored. Region is a property of the warehouse, and every query that filters by region joins `warehouses`. That matches the file: no warehouse spans two regions.

Order status is a Postgres enum: `delivered`, `delayed`, `in_transit`, `exception`, `canceled`.

## Processes

| Command | What it does |
| --- | --- |
| `pnpm dev` | Uvicorn on port 8000 and Vite on port 5173, via concurrently. |
| `pnpm db:create` | Starts Postgres from `infra/compose/docker-compose.yml`. The host port is 54329. |
| `pnpm db:make -- "message"` | Alembic autogenerate. |
| `pnpm db:migrate` | `alembic upgrade head`. |
| `pnpm db:seed` | Loads `scripts/bootstrap/data/*.json`, including the desk users. |

Docker runs Postgres only. The API and the web app run on the host. There is no application image.

`GET /health` is liveness of the process. It does not check Postgres, and it does not return versions, configuration, or dependency status.

## Bootstrap

`scripts/bootstrap/run.py export` reads the CSV and writes five JSON files under `scripts/bootstrap/data/`. Those files are the load input, so a later change to the CSV is explicit: re-export, review the diff, then load. `load` upserts in foreign-key order (clients, warehouses, carriers, products, orders) and is safe to run twice.

## Agent

A question is a short graph.

1. BAML `WriteQuery` sees the DDL for `clients`, `warehouses`, `carriers`, `products`, and `orders`, and returns one SELECT plus `plot_required`. `users` and `refresh_tokens` are not in that prompt.
2. The guard parses the statement, allows one SELECT on those five tables, then Postgres `EXPLAIN`s it and runs it read-only with a 5 second limit and a 200 row cap.
3. A bad statement or a plot with no rows goes back to `WriteQuery` with the error, at most twice. A write is refused and is not repaired.
4. BAML `ExplainRows` writes the paragraph from the rows Postgres returned.

If the key is missing or the model call fails, the service returns a problem response and does not guess.

## What is intentionally out of scope

Carrier APIs, label purchase, inventory, multi-company tenancy, and an admin UI for users. Roles are stored so a later admin surface has somewhere to live. In this slice every signed-in user can read the whole book. That is a product rule, recorded in [auth.md](auth.md), not a missing check.
