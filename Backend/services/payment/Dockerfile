FROM python:3.12-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock* /app/
COPY libs/common /app/libs/common
COPY services/payment /app/services/payment

WORKDIR /app/services/payment
RUN uv sync --frozen --no-dev || uv sync --no-dev

EXPOSE 8004
CMD ["uv", "run", "uvicorn", "payment.main:app", "--host", "0.0.0.0", "--port", "8004"]
