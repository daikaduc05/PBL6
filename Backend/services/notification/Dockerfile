# Each service builds its own image; the build context is this directory.
# When Đức's shared library (T02) lands, this moves to a Backend/-wide context
# so libs/common can be copied in — the COPY paths below change then, nothing else.

FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.7 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Dependencies resolve from uv.lock, so the image gets the exact versions the
# team develops against. --frozen fails the build if the lock is stale rather
# than silently resolving something newer.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Source comes after dependencies so editing code reuses the cached layer above.
COPY src ./src
RUN uv sync --frozen --no-dev


FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

RUN useradd --create-home --uid 1000 app

WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/src /app/src

USER app

EXPOSE 8005

# Liveness only. Readiness touches Supabase and is polled by the orchestrator
# through GET /health/ready, not by Docker.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8005/health').status==200 else 1)"

CMD ["uvicorn", "notification.main:app", "--host", "0.0.0.0", "--port", "8005"]
