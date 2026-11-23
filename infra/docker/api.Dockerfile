FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./
COPY scripts/bootstrap ./scripts/bootstrap
COPY scripts/railway/release.py ./scripts/railway/release.py
COPY scripts/railway/api-entrypoint.sh ./scripts/railway/api-entrypoint.sh
RUN chmod +x ./scripts/railway/api-entrypoint.sh

ENV PATH="/app/.venv/bin:$PATH"

CMD ["/app/scripts/railway/api-entrypoint.sh"]
