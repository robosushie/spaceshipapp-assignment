# AGENTS.md

Built with Brix. This file is the source of truth for coding agents.

## Stack

- App type: Frontend + Backend
- Frontend: Vite + React
- Frontend runtime: Node
- UI: Tailwind + shadcn
- Backend: FastAPI
- Package manager: pnpm workspaces
- Layout: UI apps, API at root
- Database: Postgres
- DB provider: Postgres Docker
- ORM: SQLAlchemy
- AI framework: LangGraph
- Testing: Vitest + Playwright
- CI/CD: GitHub Actions
- Containers: Docker
- AI tools: 

## Build

1. Read `stack.json` and `PROMPT.md`.
2. Scaffold with official CLIs. Apply every skill under the installed skills directory.
3. Always keep security, Docker for local deps, lint, `/health`, `.env.example`, and the verification gate.
4. Run the gate in `brix/verify` and fix failures before stopping.
