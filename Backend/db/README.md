# Database — Supabase (PostgreSQL)

DDL for all five bounded contexts of PBL6, targeting a single Supabase project.

## Layout

| File | Schema | Owner | Tables |
|---|---|---|---|
| `00_schemas.sql` | — | Đức | creates the 5 schemas + `pgcrypto`; **run first** |
| `01_account.sql` | `account` | Long | `users` |
| `02_content.sql` | `content` | Hà | `categories`, `lessons` |
| `03_learning.sql` | `learning` | Hà | `quizzes`, `questions`, `options`, `histories`, `favorite_lessons`, `comments` |
| `04_payment.sql` | `payment` | Long | `transactions` |
| `05_notification.sql` | `notification` | Đạt | `messages`, `settings` |
| `schema.sql` | all | — | the six files above concatenated, for a one-shot run |

All files are idempotent (`create ... if not exists`), so re-running is safe.

## One Supabase project, five schemas

`backend.md` §1 specifies a **database per service**. Supabase gives one database
(`postgres`) per project, so each service gets its **own schema** instead. The
bounded-context rules still hold:

- **No cross-schema JOINs.** A service queries only its own schema.
- **No foreign keys across schemas.** `user_id` / `lesson_id` columns in
  `learning`, `payment`, `notification` are plain `uuid` — logical references to
  `account.users.id` / `content.lessons.id`, kept in sync via RabbitMQ events.
- Hard FKs exist only *within* a schema (`lessons.category_id`,
  `questions.quiz_id`, `options.question_id`, `comments.parent_id`).

Each service's `.env` gets a `DATABASE_URL` pointing at the same host with its own
`search_path`, e.g. `...supabase.co:5432/postgres?options=-csearch_path%3Daccount`.

## How to apply

### Option A — Supabase SQL Editor (simplest)

Open the project → **SQL Editor** → paste the contents of `schema.sql` → **Run**.

### Option B — psql / any Postgres client

```bash
# session connection string from Supabase → Project Settings → Database
psql "postgresql://postgres:[PASSWORD]@db.naypwavhrtzylupgfcyd.supabase.co:5432/postgres?sslmode=require" \
  -v ON_ERROR_STOP=1 -f schema.sql
```

If your network is IPv4-only, use the pooler host from the dashboard
(`aws-0-<region>.pooler.supabase.com:5432`, user `postgres.<project-ref>`).

### Option C — Supabase CLI migrations

Copy the files into `supabase/migrations/` with timestamp prefixes
(`20260910120000_schemas.sql`, …) and run `supabase db push`.

## Divergences from `backend.md` §5 (intentional — follows the ER diagram)

| `backend.md` | This schema |
|---|---|
| `roles` + `user_roles` (M2M RBAC) | single `users.role` text column (`CUSTOMER`/`EDITOR`/`ADMIN`) |
| `refresh_tokens` table | not included — store server-side (Redis denylist) or add later |
| `users.tier` (`normal`/`vip`) | `users.is_vip` boolean + `vip_expired_at` |
| `categories.parent_id`, `slug`, `sort_order` | flat `categories (name, description)` |
| `lessons.body` + `media_assets` + `search_vector` | single `lessons.content_url_or_text` |
| `lessons.access`/`status` (`draft/pending/published`) | `is_free` boolean + `status` (`DRAFT`/`PUBLISHED`) |
| `questions.options jsonb` + `correct_option` | normalised `questions` + `options` rows with `is_correct`, plus `questions.type` |
| `lesson_attempts` (row per attempt) | `histories` — one aggregate row per `(user_id, lesson_id)` with `highest_score` |
| `payment.plans` + `payment.outbox` | dropped — `transactions` only |
| `notification.templates` | dropped |
| `notification_settings.email_enabled`, `reminder_hour` | `settings.enable_daily_reminder` + `device_token` |

## Notes

- **Not using Supabase Auth.** `account.users` is a normal table; the account
  service hashes passwords (bcrypt) and issues JWTs itself (`backend.md` §4).
- **Enums** are `text` + `CHECK`, not PG `enum` types — easier to evolve.
- **Timestamps** are `timestamptz`. The ER diagram only carries `created_at` /
  `deleted_at`; add `updated_at` + a trigger if you need it.
- **Soft delete**: `account.users` and `content.lessons` use `deleted_at`.
  App queries must filter `where deleted_at is null`.
- **RLS**: these schemas are not in Supabase's "Exposed schemas", so PostgREST
  does not serve them — the FastAPI gateway is the only entry point. If you ever
  expose a schema, enable RLS on every table in it first.
- **`histories_user_lesson_key`** (unique on `user_id, lesson_id`) encodes the
  "highest score" semantics. Drop it if you switch to storing every attempt.
