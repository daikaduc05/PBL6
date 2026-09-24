.PHONY: sync lint test dev-account migrate-account up down

sync:
	uv sync

lint:
	uv run ruff check .
	uv run ruff format --check .

test:
	uv run pytest services/account/tests -q

dev-account:
	cd services/account && uv run uvicorn account.main:app --reload --port 8001

dev-content:
	cd services/content && uv run uvicorn content.main:app --reload --port 8002

# The account.users table on Supabase already exists (created by
# Backend/db/01_account.sql before Alembic was wired up). Run this once
# to record that baseline without re-creating the table:
#   cd services/account && uv run alembic stamp head
# A genuinely fresh database uses `upgrade head` instead.
migrate-account:
	cd services/account && uv run alembic upgrade head

up:
	docker compose up -d

down:
	docker compose down
