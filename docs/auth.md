# Auth

Spaceship has two kinds of identity, and they are not the same thing.

The shipping book has clients (`CL-1023`). Those are accounts the company ships for. They do not log in.

People who use the desk are `users`. `pnpm db:seed` loads the admin and the member from `BOOTSTRAP_ADMIN_EMAIL`, `BOOTSTRAP_ADMIN_PASSWORD`, `BOOTSTRAP_MEMBER_EMAIL`, and `BOOTSTRAP_MEMBER_PASSWORD`. Both roles can read every order, the metrics, and ask questions. There is no per-order ownership and no organisation. A valid token is enough for every row in the book.

Only an admin can invite. `POST /v1/invites` stores the person with a password they cannot use and a hashed one-time token that expires in 7 days. Resend sends the raw token once, inside a link to `/accept-invite`. The API response does not include it. `POST /v1/invites/accept` sets the password and clears the token. Until a sending domain is verified, `onboarding@resend.dev` only delivers to the address on the Resend account.

A person can change their own name, title, and department with `POST /v1/me`. They cannot change their own role. The role is chosen when an admin invites them. A wrong current password on `POST /v1/me/password` uses the same 401 sentence as login.

`POST /v1/auth/forgot` always returns 204 with an empty body, whether or not the email has an account. A missing `RESEND_API_KEY` is 503 for every address. A person who already has a password receives one hashed link, valid for 1 hour, to `/reset-password`. Someone who has not accepted an invite is left on that invite link. `POST /v1/auth/reset` sets the password and clears the token. An unknown or expired token is 404. The raw token is only in the email.

Authentication answers who is calling (401). Authorization answers what they may do (403). A member who calls `POST /v1/invites` gets 403. Every other route in this slice is allowed for both roles.

## Tokens

Access token:

- JWT, algorithm pinned to HS256 in server code. The token header's `alg` is not trusted.
- Signed with `JWT_SECRET`, which must be at least 32 bytes.
- Lifetime 15 minutes (`expires_in` is 900).
- Claims: `sub` (user id), `email`, `role`, `exp`, `iat`, `iss`, `aud`.
- `iss` is `JWT_ISSUER` (default `spaceship`). `aud` is `JWT_AUDIENCE` (default `spaceship-web`).
- No password, no secret, no order data in the payload.
- Sent as `Authorization: Bearer <token>`.
- Held in memory in the web app. It is not written to `localStorage` or `sessionStorage`.

Refresh token:

- 32 random bytes, URL-safe, generated with `secrets.token_urlsafe`.
- Only the sha256 hash is stored, on `refresh_tokens`, with the user id, expiry (7 days), and `revoked_at`.
- Delivered as a cookie: name `refresh_token`, `HttpOnly`, `SameSite=Lax`, `Path=/v1/auth`, `Secure` when `COOKIE_SECURE=true`. Local HTTP leaves `Secure` off.
- Not readable by JavaScript. The Vite dev server proxies the API so the cookie is first-party in development.
- Rotated on every successful refresh: the presented token is revoked and a new one is set.
- Logout revokes the presented token and clears the cookie.
- Reuse of a revoked or unknown refresh token is 401 and does not issue a new pair.

Login and refresh return the access token in JSON. They never return the refresh token in JSON.

## Password

Passwords are hashed with argon2 via pwdlib. The hash is the only form stored. Comparison uses the library's verifier. The login response does not distinguish "no such email" from "wrong password". Both are 401 with detail `Email or password is incorrect.`

The seed password comes from the environment. It is not hard-coded in the repository.

## Login limit

`POST /v1/auth/login` allows 5 attempts per rolling 60 seconds per client address. The sixth returns 429, `Retry-After` in seconds, and a problem body. The limiter lives in the API process. Restarting the process clears it.

## Cookie and CORS

`COOKIE_SECURE` defaults to false so local HTTP works. Production must set it true behind HTTPS.

CORS allow-lists origins from `CORS_ORIGINS`. Credentials are allowed only for that list. The wildcard origin is not used.

## What the client does

1. `POST /v1/auth/login` with email and password. Keep `access_token` in React state.
2. Send it as a bearer token on `/v1/orders`, `/v1/metrics`, and `/v1/questions`.
3. On 401 from those routes, `POST /v1/auth/refresh` once. The browser sends the cookie. Replace the access token. Retry the original request once.
4. If refresh fails, drop the access token and go to `/login`.
5. Sign out calls `POST /v1/auth/logout` and drops the access token.

A full page reload loses the access token. The desk then calls refresh once before deciding the person is signed out. That is why the refresh cookie exists.

## Threat notes

- The access token is short-lived because it cannot be revoked without a denylist. Fifteen minutes is the compromise.
- The refresh token can be revoked because the hash is in Postgres, which every API process can see. This is not an in-memory session.
- XSS can still read the in-memory access token for its remaining life. The refresh token is not exposed to script. That is the reason it is a cookie and not a second JSON field.
- `JWT_SECRET` below 32 bytes fails process startup. The example file uses a placeholder the app will reject until it is replaced. The gitignored `.env` used for local development contains a generated secret.
