FROM python:3.12-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock* /app/
COPY libs/common /app/libs/common
COPY services/content /app/services/content

WORKDIR /app/services/content
RUN uv sync --frozen --no-dev || uv sync --no-dev

EXPOSE 8002
CMD ["uv", "run", "uvicorn", "content.main:app", "--host", "0.0.0.0", "--port", "8002"]

