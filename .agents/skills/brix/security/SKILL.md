---
name: security
description: "Applies the always-on Brix security baseline. Use on every project created with brix init."
---

# Security

Always on. Do not offer to skip this skill.

## Secrets and env

- Add `.env.example` that lists every key the app or `infra/compose` reads, with empty or obvious placeholder values. Never commit real secrets, `.env`, or provider credential files.
- Validate env at process startup (Zod, Pydantic Settings, or an equivalent). Fail fast on missing required keys. Do not read `process.env` / `os.environ` ad hoc inside route handlers.
- Ignore `.env` in git. Run a secret scan (for example `gitleaks` or the agent's available scanner) before the first commit.

## HTTP surface

- Prefer HTTPS and secure cookie flags in production config when the stack sets cookies. Do not put secrets in query strings or URLs.
- Keep dependency versions pinned to what the installed skills require. Do not add a package that is not required by the stack.

## Auth and object access (when auth is selected)

- Authentication answers who the caller is (401). Authorization answers what they may do (403). Check ownership or tenancy on every object read or write (OWASP API1 Broken Object Level Authorization). A valid token for the wrong object is not proof of access; prefer 404 when hiding existence is the product rule.
- Do not trust client-supplied roles, tenant ids, or prices without server-side checks.

## Containers

- Docker is for local dependencies (database, redis) when those options are selected. Compose files and Dockerfiles live under `infra/`.

## Health

`GET /health` returns a small JSON body and does not leak config, versions, stack traces, SQL, or dependency status. Do not expose connection strings. HTTP health stays separate from database liveness unless the product explicitly wants a readiness probe that checks the database.

## Infra (only when selected)

Create `infra/` only when Docker, Kubernetes + Helm, or Postgres Docker is selected. Do not put a Dockerfile, compose file, or Helm chart inside `src/` or `apps/`.

```
infra/compose/docker-compose.yml    local Postgres; Redis only when cache is selected
infra/docker/                       one Dockerfile per service that is built
infra/helm/                         only for Kubernetes + Helm (from helm create)
  Chart.yaml
  values.yaml
  templates/                        one file per Kubernetes kind (deployment.yaml, service.yaml)
```

Helm templates use dashed names and namespaced `{{ define }}` helpers (for example `mychart.fullname`). Document every key in `values.yaml`. Compose reads a gitignored env file. Do not bake secrets into an image or a committed compose override.
