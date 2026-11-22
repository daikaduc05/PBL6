FROM python:3.12-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock* /app/
COPY libs/common /app/libs/common
COPY services/learning /app/services/learning

WORKDIR /app/services/learning
RUN uv sync --frozen --no-dev || uv sync --no-dev

EXPOSE 8003
CMD ["uv", "run", "uvicorn", "learning.main:app", "--host", "0.0.0.0", "--port", "8003"]
