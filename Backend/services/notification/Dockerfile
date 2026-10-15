# Build context is Backend/, not this directory: the service depends on the
# workspace package libs/common (pbl6-common) and Docker cannot COPY above its
# context. Build with:
#   docker build -f services/notification/Dockerfile -t pbl6-notification .
FROM python:3.12-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock* /app/
COPY libs/common /app/libs/common
COPY services/notification /app/services/notification

WORKDIR /app/services/notification
RUN uv sync --frozen --no-dev || uv sync --no-dev

EXPOSE 8005
CMD ["uv", "run", "uvicorn", "notification.main:app", "--host", "0.0.0.0", "--port", "8005"]
