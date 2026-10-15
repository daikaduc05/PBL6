# notification service (M2)

Owner: Đạt · port `8005` · schema `notification` on the shared Supabase database.

Two areas live here (spec `Document/notif_spec.md`):

- **Notifications** — in-app messages, email, the 20:00 study reminder, RabbitMQ consumers (functions 8.1–8.5).
- **Recommendation** — `GET /api/v1/lessons/recommended`, rule-based then collaborative filtering (T17/T18).

They share one service because the recommender owns no data of its own —
splitting it would cost a second container and a second database for a single
endpoint.

## Run it

From the `Backend/` workspace root:

```bash
cp services/notification/.env.example services/notification/.env   # fill in DATABASE_URL
uv sync --all-groups
uv run --directory services/notification uvicorn notification.main:app --reload --port 8005
```

| URL | What |
|---|---|
| `http://localhost:8005/health` | Liveness — touches nothing |
| `http://localhost:8005/health/ready` | Readiness — runs `SELECT 1` against Supabase |
| `http://localhost:8005/docs` | Swagger UI |

```bash
uv run --directory services/notification pytest   # tests
uv run ruff check services/notification           # lint
```

## Migrations

```bash
cd services/notification

# Supabase already has messages + settings from Backend/db/05_notification.sql,
# so mark that baseline as applied instead of trying to create it again:
uv run alembic stamp 0001

# Then apply everything newer (0002 adds processed_events):
uv run alembic upgrade head
```

A fresh database (CI, a local container) skips the stamp and runs
`upgrade head` from empty — revision 0001 creates the schema itself.

| Revision | Tables |
|---|---|
| `0001` | `messages`, `settings` — mirrors `Backend/db/05_notification.sql` |
| `0002` | `processed_events` — consumer idempotency ledger |

Each service keeps its own `alembic_version` table **inside its own schema**
(`version_table_schema` in `alembic/env.py`), so the five services sharing one
Supabase database never collide.

## Connecting to Supabase

Use the **Session Pooler** host, not the direct one: the direct host is
IPv6-only without the paid add-on, and the Transaction pooler breaks asyncpg's
prepared statements. See the comments in `.env.example`.

`DATABASE_URL` carries the database password and reaches **every** schema, not
just ours. It lives in `.env`, which is gitignored. Never commit it.

## Layout

Follows the layering rule in backend.md §3 — `api → services → repositories → models`:

```
src/notification/
├── main.py                app factory, health probes, router mounting
├── config.py              NotificationSettings(BaseServiceSettings)
├── deps.py                engine, get_db, service factories
├── api/v1/                HTTP only, no business logic
├── services/              business rules, raises AppError
├── repositories/          queries only, never raises HTTP
├── models/                SQLAlchemy, schema="notification"
└── schemas/               Pydantic request/response
```

Auth, the error envelope, logging and pagination come from `pbl6_common` — this
service defines none of them.

## Reading other schemas

The recommender (T17) needs `learning.histories` and `content.lessons`; the
reminder cron (T14) needs `account.users`. Those services' internal HTTP
endpoints do not exist yet, so this service reads the tables directly — possible
because Supabase gives us one database. Four rules keep it a debt with an exit:

1. `SELECT` only. Writing to another schema is never acceptable.
2. No cross-schema `JOIN` — query each schema separately and join in Python, so
   each query maps onto one future API call.
3. All of it lives in one `readers.py`, nowhere else.
4. When Hà's internal endpoints land, only those function bodies change.
