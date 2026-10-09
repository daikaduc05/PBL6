# notification service (M2)

Owner: Đạt · port `8005` · schema `notification` on the shared Supabase database.

Two areas live here (spec `Document/project_spec_M2_notification_recommendation.md`):

- **A — Notifications**: in-app messages, email, the 20:00 study reminder, RabbitMQ consumers.
- **B — Recommendation**: `GET /api/v1/lessons/recommended`, rule-based then collaborative filtering.

They share one service and one module branch (`module/notification`) because the
recommender owns no data of its own — splitting it would cost a second
container and a second database for a single endpoint.

## Run it

```bash
cd Backend/services/notification
cp .env.example .env          # then fill in DATABASE_URL
uv sync --all-groups
uv run uvicorn notification.main:app --reload --port 8005
```

| URL | What |
|---|---|
| `http://localhost:8005/health` | Liveness — touches nothing |
| `http://localhost:8005/health/ready` | Readiness — runs `select 1` against Supabase |
| `http://localhost:8005/docs` | Swagger UI |

```bash
uv run pytest          # tests
uv run ruff check .    # lint
uv run ruff format .   # format
```

## Schema

DDL lives in `Backend/db/`, applied through the Supabase SQL Editor. **This
service does not use Alembic** (spec §0.2) — five services share one database,
so schema changes are numbered SQL files instead of five migration histories.

| File | Tables |
|---|---|
| `05_notification.sql` | `messages`, `settings` |
| `06_notification_processed_events.sql` | `processed_events` |

`models.py` follows those files; it never generates them. `create_all()` is
never called.

## Connecting to Supabase

`DATABASE_URL` carries the database password and grants access to **every**
schema, not just ours. It goes in `.env`, which is gitignored. Never commit it.

Use the pooler host (`aws-0-<region>.pooler.supabase.com`) unless your network
has IPv6 — the direct host is IPv6-only on the free plan. The pooler runs
pgbouncer in transaction mode, where asyncpg's prepared statements collide
across clients and raise `DuplicatePreparedStatementError` at random, so
`DB_DISABLE_STATEMENT_CACHE=true` (the default) turns that cache off.

## Reading other schemas

The recommender needs `learning.histories` and `content.lessons`; the reminder
cron needs `account.users`. Those services' HTTP endpoints do not exist yet, so
this service reads the tables directly — possible because Supabase gives us one
database. Four rules keep it a debt with an exit (spec §0.4):

1. `SELECT` only. Writing to another schema is never acceptable.
2. No cross-schema `JOIN` — query each schema separately, join in Python, so
   each query maps onto one future API call.
3. All of it lives in `readers.py`, nowhere else.
4. When Hà's internal endpoints land, only those function bodies change.

## Layout

```
src/notification/
├── main.py          app factory, health probes, router mounting
├── config.py        pydantic-settings, lazily read
├── db.py            async engine, session dependency
├── models.py        messages, settings, processed_events
├── deps.py          X-User-Id → CurrentUser        (TODO: pbl6_common at T02)
├── errors.py        error envelope                  (TODO: pbl6_common at T02)
├── notifications/   area A
└── recommendation/  area B
```

`deps.py` and `errors.py` are deliberate stand-ins for Đức's shared library
(T02). They are kept minimal so replacing them is a delete, not a rewrite.
