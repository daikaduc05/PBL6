FROM python:3.12-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock* /app/
COPY libs/common /app/libs/common
COPY services/account /app/services/account

WORKDIR /app/services/account
RUN uv sync --frozen --no-dev || uv sync --no-dev

EXPOSE 8001
CMD ["uv", "run", "uvicorn", "account.main:app", "--host", "0.0.0.0", "--port", "8001"]
