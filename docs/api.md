# API

The service is FastAPI. The contract that clients should trust is the generated OpenAPI document at `/openapi.json` (UI at `/docs`). This file is the map of that document: resources, status codes, and the error shape. If the two disagree, the running schema wins and this file should be updated.

All versioned routes are mounted once under `/v1`. Route modules do not repeat `v1` in their filenames.

## Inventory

| Method and path | Auth | Purpose |
| --- | --- | --- |
| `GET /health` | Public | Process is up. Body is `{"status":"ok"}`. |
| `POST /v1/auth/login` | Public | Exchange email and password for an access token. Sets the refresh cookie. |
| `POST /v1/auth/refresh` | Refresh cookie | Rotate the refresh token and return a new access token. |
| `POST /v1/auth/logout` | Refresh cookie | Revoke the refresh token and clear the cookie. |
| `POST /v1/auth/forgot` | Public | Email a one-hour reset link. Always 204. Missing Resend key is 503. |
| `POST /v1/auth/reset` | Public | Set a password from the reset token and clear it. |
| `GET /v1/me` | Bearer | The signed-in person: id, email, name, title, department, role. |
| `POST /v1/me` | Bearer | Update own name, title, and department. Role is not accepted. |
| `POST /v1/me/password` | Bearer | Change password. Wrong current password is 401. |
| `POST /v1/invites` | Bearer, admin | Email a set-password link. A member is 403. A duplicate email is 409. |
| `POST /v1/invites/accept` | Public | Set a password from the invite token and clear it. |
| `GET /v1/orders` | Bearer | Page of orders. |
| `GET /v1/orders/{order_id}` | Bearer | One order. |
| `GET /v1/metrics` | Bearer | Totals for the desk charts. |
| `POST /v1/questions` | Bearer | Ask one question about the book. |
| `POST /v1/chat-titles` | Bearer | A short tab title from the first question, written by gpt-5-nano. |

`GET /health`, `POST /v1/auth/login`, `POST /v1/auth/forgot`, `POST /v1/auth/reset`, and `POST /v1/invites/accept` are public. Refresh and logout authenticate with the cookie rather than the bearer token.

## Orders

`GET /v1/orders`

Query parameters, all optional except pagination defaults:

- `status` — one of `delivered`, `delayed`, `in_transit`, `exception`, `canceled`
- `region` — exact warehouse region
- `carrier` — carrier name, exact match
- `client_id` — exact match
- `filter` — repeatable. Each value is `column:operator:value`, at most 8. Columns are `order_id`, `client_id`, `order_date`, `delivery_date`, `carrier`, `warehouse`, `region`, `origin_city`, `destination_city`, `status`, `sku`, `category`, `quantity`, `unit_price_usd`, `order_value_usd`, `promo`. Text operators are `contains` and `equals`. Dates are `on`, `before`, `after`, and `empty` (no value). Numbers are `equals`, `gt`, and `lt`. Status and promo use `is` (`yes` or `no` for promo). An unknown column, operator, or value is 422.
- `limit` — default 10, maximum 50. Above 50 is 422.
- `offset` — default 0. Negative is 422.

Sort is fixed: `order_date` descending, `order_id` descending. The client does not pick the sort.

```json
{
  "items": [
    {
      "order_id": "ORD-2026-267300-0001",
      "client_id": "CL-1023",
      "order_date": "2025-10-19",
      "delivery_date": "2025-10-22",
      "carrier": "DHL",
      "origin_city": "London, UK",
      "destination_city": "Leeds, UK",
      "status": "delivered",
      "sku": "PAPER-0197",
      "product_category": "PAPER",
      "quantity": 2,
      "unit_price_usd": "13.11",
      "order_value_usd": "26.22",
      "is_promo": false,
      "promo_discount_pct": 0,
      "region": "UK",
      "warehouse": "LON-FC1"
    }
  ],
  "total": 400,
  "offset": 0
}
```

Money is a decimal string so a float cannot round it. `delivery_date` is `null` when the shipment has not arrived or was canceled.

`GET /v1/orders/{order_id}` returns the same object. An unknown id is 404.

## Metrics

`GET /v1/metrics` returns the numbers the desk draws. It is not a general aggregation language.

```json
{
  "totals": {
    "orders": 400,
    "revenue_usd": "0.00",
    "delayed": 55,
    "exceptions": 11,
    "in_transit": 27
  },
  "carriers": 6,
  "warehouses": 8,
  "clients": 24,
  "products": 12,
  "deliveries_last_month": 40,
  "by_status": [{ "status": "delivered", "count": 304 }],
  "by_region": [{ "region": "UK", "orders": 54, "revenue_usd": "0.00" }],
  "by_carrier": [{ "carrier": "FedEx", "orders": 89, "delayed": 0, "exceptions": 0 }]
}
```

`by_status` includes every status, including those with a zero count, in the enum order. `revenue_usd` is the sum of `order_value_usd`. Promo percent is not subtracted. `carriers`, `warehouses`, `clients`, and `products` are row counts of those tables. `deliveries_last_month` counts orders with status `delivered` and a `delivery_date` from 2025-12-01 through 2025-12-30, the book's current month.

## Questions

`POST /v1/questions`

```json
{ "question": "How many DHL orders into the UK were delayed?" }
```

`question` is a string from 1 to 500 characters. Anything else is 422.

```json
{
  "answer": "…",
  "plot_required": true,
  "chart": {
    "type": "bar",
    "title": "Delivered orders by week",
    "x_key": "week",
    "y_keys": ["orders"],
    "rows": [{ "week": "2025-10-06", "orders": "12" }]
  }
}
```

The model sees the shipping-book schema and writes one PostgreSQL `SELECT`. It sets `plot_required` from the question. `chart` is null when `plot_required` is false. `chart.type` is `bar`, `line`, `area`, `pie`, or `scatter`, chosen from the question: line or area for time, bar for categories, pie for one share across a few categories, scatter for two numeric columns. `x_key` and `y_keys` are column aliases from that query, and `rows` are what Postgres returned, capped at 200. The model does not choose the numbers. A query that is not a single `SELECT` on `clients`, `warehouses`, `carriers`, `products`, or `orders` is rejected. `users` and `refresh_tokens` are not in the prompt. Relative ranges such as "last 3 months" are counted from the book end, 2025-12-30. If the query cannot be repaired twice, the answer is "The question could not be queried." and `plot_required` is false.

When `ANTHROPIC_API_KEY` is empty the status is 503 and the body is a problem document. The response does not say whether the key is missing versus rejected by Anthropic in a way that leaks the key. The detail is a single sentence: the question service is unavailable.

## Auth bodies

Login:

```json
{ "email": "admin@spaceship.local", "password": "…" }
```

Success is 200:

```json
{
  "access_token": "<jwt>",
  "token_type": "Bearer",
  "expires_in": 900
}
```

The refresh token is not in the JSON. It is `Set-Cookie` on `refresh_token`. See [auth.md](auth.md).

Refresh and logout take no body. Refresh returns the same access-token object. Logout returns 204 and an empty body.

Authenticated routes expect `Authorization: Bearer <access_token>`. A missing or invalid token is 401. A well-formed token for a deleted user is 401.

Forgot password takes `{ "email": "ada@example.com" }` and returns 204 with an empty body for every address. Reset takes the token from the email:

```json
{ "token": "<from the email>", "password": "a-new-password" }
```

Success is 204. An unknown or expired token is 404. The link lasts 1 hour.

Profile update:

```json
{ "name": "Ada", "title": "Ops lead", "department": "Logistics" }
```

The response still includes `role`. Sending `role` does not change it.

Password change takes `current_password` and `new_password` (at least 8 characters) and returns 204.

Invite:

```json
{ "name": "Grace", "email": "grace@example.com", "role": "member", "title": "Ops", "department": "Logistics" }
```

Success is 201 with `{ "email": "grace@example.com" }`. The token is only in the email. Accept invite is public:

```json
{ "token": "<from the email>", "password": "a-new-password" }
```

Success is 204. An unknown or expired token is 404. Invites need `RESEND_API_KEY`. Without it, or if Resend rejects the message, the status is 503 and no account is kept. `RESEND_FROM` defaults to `onboarding@resend.dev`, which only delivers to the Resend account address until a domain is verified. `WEB_ORIGIN` builds the link.

## Errors

Failures use `Content-Type: application/problem+json` (RFC 9457).

```json
{
  "type": "https://spaceship.local/problems/validation-error",
  "title": "Validation failed",
  "status": 422,
  "detail": "Request failed validation.",
  "instance": "/v1/orders"
}
```

Field errors add `errors`:

```json
{
  "errors": [
    { "pointer": "/limit", "detail": "Input should be less than or equal to 50" }
  ]
}
```

`pointer` is a JSON Pointer. Query parameters use a pointer of `/limit`, not a query-string fragment.

| Status | When |
| --- | --- |
| 400 | JSON is not JSON, or a cursor-like value is garbage. This slice uses offset, so 400 is mainly broken JSON. |
| 401 | No caller, bad password, unknown email, bad or expired token. Unknown email and wrong password share one detail: `Email or password is incorrect.` |
| 403 | Reserved. This slice has no route that returns it. A signed-in user may read every order. |
| 404 | Order id is not in the book. |
| 422 | JSON parsed, a field or query value failed a rule. `limit` above 50. Empty question. |
| 429 | Login more than 5 times in a rolling minute from the same client address. `Retry-After` is set, in seconds. |
| 503 | Question asked while the model is not configured. |

The HTTP status and the body's `status` field match. A 200 response is never an error. Bodies do not contain stack traces, SQL, file paths, or connection strings.

## Pagination

Offset is used because the book is 400 rows and the desk is a table you jump around, not a feed. `limit` default 10, max 50, enforced on the server. The response is `items`, `total`, and `offset`.

## CORS and the browser

In development the Vite server proxies `/v1` and `/health` to `http://127.0.0.1:8000`. The browser talks to one origin, so the refresh cookie is same-site. CORS still allow-lists `CORS_ORIGINS` (default `http://localhost:5173`) for any client that calls the API directly. The allow-list is never `*` combined with credentials. `Authorization` and `Content-Type` are the allowed request headers.

## Rate limit

Login is limited to 5 requests per minute per client address, in the API process. That counter is per process. It is a local-dev control, not a multi-instance gateway. Other routes are not limited in this slice.
