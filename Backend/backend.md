# Backend — Technical Document

**Project:** English Self-Study Platform (PBL6)
**Stack:** FastAPI (Python 3.12) · PostgreSQL · RabbitMQ · Docker Compose · Nginx
**Owners:** Đức (infrastructure, gateway) · Đạt (notification, recommendation) · Long (account, payment) · Hà (content, learning) · Ninthanon (simple CRUD, seed, QA)

> **Note on the assignment sheet.** `Document/phan_cong_do_an_tu_hoc_tieng_anh.xlsx` specifies a **NestJS** monorepo. This project uses **FastAPI** instead. The bounded contexts, module ownership, event contracts and sprint plan from the sheet are unchanged — only the runtime differs. Tasks T01–T07 (monorepo, common lib, Jest, CI) map to the Python equivalents described in §9 and §11.

---

## 1. Architecture Overview

Six independently deployable services behind a single gateway. Each business service owns its own PostgreSQL database. **No cross-service SQL JOINs** — services reference each other only by ID and synchronise state through RabbitMQ events.

```
   Web (Next.js)  ---+
                     |
   Mobile (Expo)  ---+---->  Nginx (reverse proxy)  ---->  API Gateway  :8000
                                                                 |
                                                                 |  internal HTTP
        +------------+---------------+-----------+---------------+--------------+
        v            v               v           v               v              v
    account      content         learning     payment      notification   (recommendation
     :8001        :8002           :8003        :8004           :8005       lives in notif)
        |            |               |           |               |
    account_db   content_db     learning_db  payment_db   notification_db
        |            |               |           |               |
        +------------+---------------+-----+-----+---------------+
                                           v
                          RabbitMQ  --  topic exchange "pbl6.events"
```

### Why this shape

| Decision | Reason |
|---|---|
| Database per service | Each owner migrates their schema without coordinating with the other four. Enforces the bounded context. |
| Gateway verifies JWT | Services trust the gateway's forwarded user context, so auth logic lives in exactly one place. |
| RabbitMQ for cross-service state | A VIP upgrade after payment must not be a synchronous chain of four HTTP calls. |
| Outbox pattern in payment | The transaction row and its `payment.succeeded` event are written in the same DB transaction, so a crash cannot lose the event. |

---

## 2. Services

| Code | Service | Port | Owner | Database | Responsibility |
|---|---|---|---|---|---|
| M1 | `gateway` | 8000 | Đức | — (stateless) | Routing, JWT verification, RBAC pre-check, rate limiting, security headers, admin statistics fan-out |
| M3 | `account` | 8001 | Long | `account_db` | Register / login / refresh, RBAC, student & editor management, VIP lifecycle, search |
| M5 | `content` | 8002 | Hà | `content_db` | Category & lesson CRUD, difficulty levels, S3 media, full-text search, DRAFT→PENDING→PUBLISHED moderation |
| M6 | `learning` | 8003 | Hà | `learning_db` | Quizzes, auto-grading, attempt history, favorites, comments, `last-activity` internal API |
| M4 | `payment` | 8004 | Long | `payment_db` | VNPay/Momo checkout, webhook verification, outbox + relay worker |
| M2 | `notification` | 8005 | Đạt | `notification_db` | In-app + email notifications, 20:00 study-reminder cron, event consumers, `/lessons/recommended` |

### Service boundaries — hard rules

1. `account` is the **only** owner of `user_id`. Other services store the UUID and nothing else. No foreign keys across databases.
2. A service never reads another service's database. Cross-context reads go through the gateway or an explicit internal endpoint (e.g. `GET /internal/learning/last-activity`).
3. VIP status is **eventually consistent**. `payment` publishes `payment.succeeded`; `account` consumes it and upgrades the user. Clients must tolerate a window where payment is done but VIP is not yet visible.

---

## 3. Repository Layout

```
Backend/
├── pyproject.toml              # uv workspace root + shared tool config
├── uv.lock
├── docker-compose.yml          # 5 postgres + rabbitmq + redis + nginx + 6 services
├── .env.example
├── Makefile                    # make up / test / lint / migrate / seed
├── nginx/
│   └── nginx.conf
├── libs/
│   └── common/                 # editable workspace package "pbl6-common"
│       └── src/pbl6_common/
│           ├── config.py       # pydantic-settings BaseSettings
│           ├── db.py           # async engine, session factory, declarative Base
│           ├── security.py     # JWT encode/decode, password hashing
│           ├── deps.py         # get_db, get_current_user, require_role, require_vip
│           ├── errors.py       # AppError hierarchy + exception handlers
│           ├── logging.py      # structlog JSON logger carrying request_id
│           ├── pagination.py
│           └── events/
│               ├── schemas.py  # Pydantic model for every event payload
│               ├── publisher.py
│               └── consumer.py
└── services/
    ├── gateway/
    ├── account/
    ├── content/
    ├── learning/
    ├── payment/
    └── notification/
```

Every service uses the same internal layout:

```
services/account/
├── pyproject.toml              # depends on pbl6-common
├── Dockerfile
├── alembic.ini
├── alembic/versions/
├── src/account/
│   ├── main.py                 # app factory, routers, middleware, lifespan
│   ├── api/v1/                 # routers — HTTP layer only, no business logic
│   ├── schemas/                # Pydantic request/response models
│   ├── models/                 # SQLAlchemy ORM models
│   ├── services/               # business logic (the only layer allowed to be complex)
│   ├── repositories/           # database queries
│   └── events/                 # publishers and consumers for this context
└── tests/
    ├── unit/
    └── integration/
```

**Layering rule:** `api → services → repositories → models`. A router must never build a SQLAlchemy query; a repository must never raise an HTTP exception.

---

## 4. Technology Choices

| Concern | Choice | Notes |
|---|---|---|
| Runtime | Python 3.12 | Pinned in `.python-version` and every Dockerfile |
| Framework | FastAPI 0.115+ | Automatic OpenAPI, native async, Pydantic validation |
| ASGI server | Uvicorn (dev) / Gunicorn + UvicornWorker (prod) | 2 workers per service container |
| ORM | SQLAlchemy 2.0 async + `asyncpg` | Typed 2.0 style (`Mapped[...]`), not the legacy Query API |
| Migrations | Alembic | One migration history **per service** |
| Validation | Pydantic v2 + pydantic-settings | All config from env vars, no hardcoded secrets |
| Messaging | RabbitMQ via `aio-pika` | Topic exchange `pbl6.events`, durable queues, DLQ per consumer |
| Scheduling | APScheduler (AsyncIOScheduler) | Study reminder 20:00, VIP expiry sweep 00:00, outbox relay every 5s |
| Auth | `python-jose` (JWT) + `passlib[bcrypt]` | Access 15 min, refresh 7 days |
| Object storage | AWS S3 via `boto3` | Presigned upload URLs; CDN URL returned to the client |
| Cache / rate limit | Redis | Gateway rate limiting + refresh-token denylist |
| Package manager | `uv` | Workspace support, reproducible and fast in CI |
| Lint + format | `ruff` | Replaces flake8 + isort + black |
| Type check | `mypy` — strict on `libs/`, normal on services | |
| Tests | `pytest`, `pytest-asyncio`, `httpx.AsyncClient`, `testcontainers` | |

---

## 5. Data Model (per database)

### `account_db` — Long
- `users` — `id (uuid pk)`, `email (unique)`, `password_hash`, `full_name`, `status (active\|locked)`, `tier (normal\|vip)`, `vip_expiry (date, null)`, timestamps
- `roles` — `id`, `name (admin\|editor\|student)`
- `user_roles` — `user_id`, `role_id` (composite pk)
- `refresh_tokens` — `id`, `user_id`, `token_hash`, `expires_at`, `revoked_at`

### `content_db` — Hà
- `categories` — `id`, `parent_id (self fk, nullable)`, `name`, `slug`, `sort_order`
- `lessons` — `id`, `category_id`, `title`, `body`, `level (easy\|medium\|hard)`, `access (public\|vip)`, `status (draft\|pending\|published)`, `search_vector (tsvector)`, timestamps
- `media_assets` — `id`, `lesson_id`, `kind (audio\|image)`, `s3_key`, `cdn_url`, `bytes`

GIN index on `lessons.search_vector`, maintained by a trigger — this is task T38.

### `learning_db` — Hà
- `quizzes` — `id`, `lesson_id (uuid, no FK — cross-context)`, `title`, `pass_score`
- `questions` — `id`, `quiz_id`, `prompt`, `options (jsonb)`, `correct_option` — **never serialised to students**
- `lesson_attempts` — `id`, `user_id`, `quiz_id`, `score`, `duration_seconds`, `answers (jsonb)`, `submitted_at`
- `favorites` — `user_id`, `lesson_id` (composite pk)
- `comments` — `id`, `lesson_id`, `user_id`, `body`, `created_at`, `deleted_at`

### `payment_db` — Long
- `plans` — `id`, `code`, `name`, `price_vnd`, `duration_days`
- `transactions` — `id`, `user_id`, `plan_id`, `amount_vnd`, `provider (vnpay\|momo)`, `provider_txn_ref (unique)`, `status (pending\|succeeded\|failed)`, timestamps
- `outbox` — `id`, `aggregate_id`, `event_type`, `payload (jsonb)`, `created_at`, `published_at (nullable)`

### `notification_db` — Đạt
- `templates` — `id`, `code`, `channel (email\|in_app)`, `subject`, `body_template`
- `notifications` — `id`, `user_id`, `template_code`, `title`, `body`, `read_at`, `created_at`
- `notification_settings` — `user_id (pk)`, `study_reminder (bool)`, `email_enabled (bool)`, `reminder_hour (int, default 20)`

---

## 6. Event Contract (task T04)

Exchange `pbl6.events`, type `topic`, durable. Every consumer binds its own durable queue plus a dead-letter queue `<queue>.dlq` after 3 failed deliveries.

Envelope — identical for every event:

```json
{
  "event_id": "uuid",
  "event_type": "payment.succeeded",
  "version": 1,
  "occurred_at": "2026-09-09T13:40:00Z",
  "producer": "payment-service",
  "data": {}
}
```

| Routing key | Producer | Consumers | `data` |
|---|---|---|---|
| `payment.succeeded` | payment | account, notification | `{ transaction_id, user_id, plan_id, amount_vnd, duration_days }` |
| `payment.failed` | payment | notification | `{ transaction_id, user_id, reason }` |
| `account.locked` | account | notification | `{ user_id, locked_by, reason }` |
| `account.unlocked` | account | notification | `{ user_id }` |
| `vip.expired` | account | notification | `{ user_id, expired_at }` |
| `lesson.published` | content | notification | `{ lesson_id, title, category_id }` |

**Rules:** consumers must be idempotent (dedupe on `event_id`); `version` is bumped rather than changing a field's meaning; a consumer ignores event types and fields it does not recognise.

---

## 7. API Conventions

- Base path `/api/v1`. JSON only, `snake_case` field names.
- Pagination: `?page=1&size=20` → `{ "items": [], "total": 0, "page": 1, "size": 20 }`.
- Errors use one shape everywhere, produced by the shared exception handler:

```json
{
  "error": {
    "code": "ACCOUNT_NOT_FOUND",
    "message": "User does not exist",
    "details": null,
    "request_id": "01J..."
  }
}
```

| Status | When |
|---|---|
| 400 | Malformed request |
| 401 | Missing / invalid / expired token |
| 403 | Authenticated but role or tier insufficient (includes non-VIP hitting VIP content) |
| 404 | Resource does not exist |
| 409 | Conflict — duplicate email, double submit |
| 422 | Pydantic validation failure (FastAPI default, reshaped into the envelope above) |
| 429 | Rate limit exceeded |

### Auth flow

1. `POST /api/v1/auth/login` → `{ access_token, refresh_token, expires_in }`
2. The client sends `Authorization: Bearer <access_token>`.
3. The **gateway** decodes and verifies the JWT, then forwards the request downstream with `X-User-Id`, `X-User-Roles`, `X-User-Tier`, `X-Request-Id`.
4. Downstream services trust those headers **only** because they are unreachable from outside the Docker network. They still re-check role and tier for their own endpoints.
5. `POST /api/v1/auth/refresh` rotates the refresh token and revokes the old one.

JWT claims: `sub` (user_id), `roles`, `tier`, `exp`, `iat`, `jti`.

### Selected endpoints

```
POST   /api/v1/auth/register              public
POST   /api/v1/auth/login                 public
POST   /api/v1/auth/refresh               public
GET    /api/v1/users/me                   authenticated
PATCH  /api/v1/users/me                   authenticated
GET    /api/v1/admin/users                admin
PATCH  /api/v1/admin/users/{id}/status    admin          lock / unlock

GET    /api/v1/categories                 public
GET    /api/v1/lessons?level=&category=   public         VIP lessons return a teaser only
GET    /api/v1/lessons/{id}               public / vip
POST   /api/v1/lessons                    editor
POST   /api/v1/lessons/{id}/submit        editor         -> PENDING
POST   /api/v1/lessons/{id}/approve       admin          -> PUBLISHED
GET    /api/v1/search?q=                  public

GET    /api/v1/quizzes/{lesson_id}        authenticated  answers stripped
POST   /api/v1/quizzes/{id}/submit        authenticated  returns score immediately
GET    /api/v1/me/attempts                authenticated
GET    /internal/learning/last-activity   internal only

POST   /api/v1/payments/checkout          authenticated  -> { redirect_url }
POST   /api/v1/payments/webhook/{provider} public        signature-verified

GET    /api/v1/notifications              authenticated
PATCH  /api/v1/notifications/{id}/read    authenticated
GET    /api/v1/lessons/recommended        authenticated
GET    /api/v1/admin/stats                admin          gateway fan-out
```

Every service exposes `GET /health` (liveness) and `GET /health/ready` (database + broker reachable). The gateway aggregates all six OpenAPI schemas at `/docs` (task T07).

---

## 8. Local Development

```bash
cd Backend
cp .env.example .env
uv sync                       # install workspace + all service dependencies
docker compose up -d          # postgres x5, rabbitmq, redis, nginx
make migrate                  # alembic upgrade head for every service
make seed                     # demo accounts + 20 lessons + 5 quizzes (task T57)
make dev                      # run all six services with --reload
```

| URL | What |
|---|---|
| `http://localhost:8080` | Nginx → gateway |
| `http://localhost:8000/docs` | Aggregated Swagger UI |
| `http://localhost:15672` | RabbitMQ management (guest / guest) |

Demo accounts after `make seed`: `admin@pbl6.dev`, `editor@pbl6.dev`, `vip@pbl6.dev`, `student@pbl6.dev` — password `Password123!`.

### Adding a migration

```bash
cd services/account
uv run alembic revision --autogenerate -m "add vip_expiry to users"
uv run alembic upgrade head
```

Migrations run automatically on container start in deployed environments.

---

## 9. Quality Gates

Enforced by CI on every push and pull request — see [backend-ci.yml](../.github/workflows/backend-ci.yml) and §11.

| Gate | Command | Blocks merge |
|---|---|---|
| Syntax | `python -m compileall -q services libs` | yes |
| Lint | `ruff check .` | yes |
| Format | `ruff format --check .` | yes |
| Types | `mypy services libs` | yes |
| Tests | `pytest --cov=services --cov=libs` | yes |
| Image build | `docker build` per service | yes |

Coverage target 60% on `services/*/src/*/services/` — the business-logic layer. Routers and models are not counted.

### Testing approach

- **Unit** — business-logic functions with repositories replaced by fakes. No database, no network. Should be the majority of tests.
- **Integration** — router plus a real PostgreSQL from `testcontainers`, one throwaway database per test module.
- **Contract** — every event publisher has a test asserting its payload validates against the Pydantic schema in `libs/common/events/schemas.py`. This is what stops one owner silently breaking another owner's consumer.
- **E2E** — Postman collection run by Newman against `docker compose up` (task T58).

---

## 10. Configuration

All configuration comes from environment variables via `pydantic-settings`. Nothing is read from a file at runtime; `.env` is a developer convenience and is git-ignored.

```env
ENV=local                       # local | staging | production
LOG_LEVEL=INFO

DATABASE_URL=postgresql+asyncpg://pbl6:pbl6@localhost:5432/account_db
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
REDIS_URL=redis://localhost:6379/0

JWT_SECRET=change-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_MINUTES=15
REFRESH_TOKEN_DAYS=7

AWS_REGION=ap-southeast-1
S3_BUCKET=pbl6-media
CDN_BASE_URL=https://cdn.example.com

SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=

VNPAY_TMN_CODE=
VNPAY_HASH_SECRET=
MOMO_PARTNER_CODE=
MOMO_ACCESS_KEY=
MOMO_SECRET_KEY=
```

Secrets for CI/CD live in GitHub Actions repository secrets. **A secret must never appear in a commit.**

---

## 11. CI/CD

Pipeline [backend-ci.yml](../.github/workflows/backend-ci.yml) runs on push and pull request touching `Backend/**`:

```
  syntax          python -m compileall        ~5s, fails fast on a typo
     |
     v
  quality         ruff check
                  ruff format --check
                  mypy
     |
     v
  test            pytest, with postgres + rabbitmq service containers
     |
     v
  docker (x6)     docker build per service, layer-cached, not pushed on PRs
```

The `syntax` job exists so an obvious typo fails in seconds rather than after a full dependency install. CD to the VPS (task T06) is deliberately **not** in this pipeline yet — add it once staging secrets exist.

---

## 12. Security Checklist

- [ ] Passwords hashed with bcrypt, cost ≥ 12. Never logged.
- [ ] JWT secret ≥ 32 random bytes, different per environment.
- [ ] Refresh tokens stored hashed, rotated on use, revoked on logout.
- [ ] Rate limit at the gateway: 100 req/min/IP globally, 5 req/min/IP on `/auth/login` (task T10).
- [ ] Security headers at the gateway: `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, `Referrer-Policy`.
- [ ] CORS allow-list is explicit — never `*` together with credentials.
- [ ] SQL only through SQLAlchemy parameter binding; no f-string queries.
- [ ] Payment webhooks verify the provider signature **before** parsing the body, and are idempotent on `provider_txn_ref`.
- [ ] S3 uploads use presigned URLs with a content-type restriction and a 10 MB cap.
- [ ] Quiz answers stripped in the response schema, not in the frontend.
- [ ] Internal endpoints (`/internal/*`) rejected by Nginx when the request originates outside the Docker network.

---

## 13. Known Risks

| Risk | Mitigation |
|---|---|
| Gateway JWT verification (T09) depends on Auth (T21) | Đức uses a locally-signed mock token with the same claims until Auth lands |
| Payment sandbox unavailable during the demo | A `MOCK_PAYMENT=true` flag makes checkout return a fake redirect and publish `payment.succeeded` directly |
| VIP not applied immediately after payment | Documented as eventual consistency; the result page polls `GET /users/me` for up to 10s and shows a "processing" state |
| Five separate migration histories drift apart | `make migrate` runs all five in a fixed order; CI runs it against a clean database on every PR |
