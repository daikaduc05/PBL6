-- ==========================================================================
-- 00_schemas.sql  —  run this FIRST
--
-- One Supabase project hosts all five bounded contexts. Each service gets its
-- own PostgreSQL schema instead of its own database (backend.md §1 asks for a
-- "database per service"; on a single Supabase project a schema per service is
-- the closest equivalent and still forbids cross-context JOINs by convention).
--
-- Cross-service references (user_id, lesson_id in other schemas) are LOGICAL
-- only — no foreign keys cross a schema boundary, matching backend.md's
-- "no foreign keys across databases" rule.
-- ==========================================================================

create extension if not exists pgcrypto;   -- gen_random_uuid() (native on PG13+, kept for safety)

create schema if not exists account;
create schema if not exists content;
create schema if not exists learning;
create schema if not exists payment;
create schema if not exists notification;

comment on schema account      is 'M3 account service — users, RBAC, VIP lifecycle (owner: Long)';
comment on schema content      is 'M5 content service — categories & lessons (owner: Ha)';
comment on schema learning     is 'M6 learning service — quizzes, attempts, favorites, comments (owner: Ha)';
comment on schema payment      is 'M4 payment service — transactions (owner: Long)';
comment on schema notification is 'M2 notification service — messages & settings (owner: Dat)';
-- ==========================================================================
-- 01_account.sql  —  account service (owner: Long)
-- Bounded context M3. Sole owner of user identity; every other schema stores
-- users.id as an unconstrained uuid.
--
-- Note: this project does NOT use Supabase Auth. The account service does its
-- own register/login (bcrypt hash + JWT) per backend.md §4, so users live here
-- as a plain table, not in auth.users.
-- ==========================================================================

set search_path = account, public;

create table if not exists account.users (
    id             uuid        primary key default gen_random_uuid(),
    email          text        not null,
    password_hash  text        not null,
    full_name      text        not null,
    role           text        not null default 'CUSTOMER'
                       check (role in ('CUSTOMER', 'EDITOR', 'ADMIN')),
    status         text        not null default 'ACTIVE'
                       check (status in ('ACTIVE', 'INACTIVE', 'LOCKED')),
    is_vip         boolean     not null default false,
    vip_expired_at timestamptz,
    created_at     timestamptz not null default now(),
    deleted_at     timestamptz
);

-- Unique email. Plain UNIQUE per backend.md ("email (unique)"). If you want to
-- allow re-registration of a soft-deleted address, swap for the partial index
-- in the commented block below.
create unique index if not exists users_email_key on account.users (lower(email));
-- drop index account.users_email_key;
-- create unique index users_email_active_key
--     on account.users (lower(email)) where deleted_at is null;

create index if not exists users_role_idx   on account.users (role);
create index if not exists users_status_idx on account.users (status);
create index if not exists users_vip_idx    on account.users (is_vip, vip_expired_at)
    where is_vip;

comment on table  account.users              is 'Registered accounts. Soft-deleted via deleted_at.';
comment on column account.users.role         is 'CUSTOMER | EDITOR | ADMIN';
comment on column account.users.status       is 'ACTIVE | INACTIVE | LOCKED';
comment on column account.users.is_vip       is 'Set by consuming payment.succeeded; eventually consistent';
comment on column account.users.vip_expired_at is 'Null when not VIP; swept by the 00:00 VIP-expiry job';
-- ==========================================================================
-- 02_content.sql  —  content service (owner: Ha)
-- Bounded context M5. Categories and lessons.
-- ==========================================================================

set search_path = content, public;

create table if not exists content.categories (
    id          uuid primary key default gen_random_uuid(),
    name        text not null,
    description text
);

comment on table content.categories is 'Lesson categories (flat, no parent_id in this schema).';

create table if not exists content.lessons (
    id                  uuid        primary key default gen_random_uuid(),
    category_id         uuid        not null
                            references content.categories (id) on delete restrict,  -- hard FK, same schema
    title               text        not null,
    content_url_or_text text,
    level               text        not null default 'EASY'
                            check (level in ('EASY', 'MEDIUM', 'HARD')),
    is_free             boolean     not null default true,
    status              text        not null default 'DRAFT'
                            check (status in ('DRAFT', 'PUBLISHED')),
    deleted_at          timestamptz
);

create index if not exists lessons_category_idx on content.lessons (category_id);
create index if not exists lessons_status_idx   on content.lessons (status)
    where deleted_at is null;
create index if not exists lessons_level_idx    on content.lessons (level);

comment on table  content.lessons                     is 'Lessons. Soft-deleted via deleted_at.';
comment on column content.lessons.content_url_or_text is 'Inline text or a CDN/S3 URL to the lesson body';
comment on column content.lessons.is_free            is 'false => VIP-only; non-VIP users get a teaser';
comment on column content.lessons.status             is 'DRAFT | PUBLISHED';
-- ==========================================================================
-- 03_learning.sql  —  learning service (owner: Ha)
-- Bounded context M6. Quizzes, questions, options, attempt history,
-- favorites, threaded comments.
--
-- lesson_id / user_id are LOGICAL foreign keys to the content / account
-- schemas — intentionally left unconstrained (bounded context rule).
-- ==========================================================================

set search_path = learning, public;

-- --- Quiz structure ------------------------------------------------------

create table if not exists learning.quizzes (
    id         uuid        primary key default gen_random_uuid(),
    lesson_id  uuid        not null,                    -- logical FK -> content.lessons.id
    title      text        not null,
    created_at timestamptz not null default now()
);
create index if not exists quizzes_lesson_idx on learning.quizzes (lesson_id);

create table if not exists learning.questions (
    id      uuid primary key default gen_random_uuid(),
    quiz_id uuid not null references learning.quizzes (id) on delete cascade,  -- hard FK
    content text not null,
    type    text not null default 'SINGLE_CHOICE'
                check (type in ('SINGLE_CHOICE', 'MULTI_CHOICE'))
);
create index if not exists questions_quiz_idx on learning.questions (quiz_id);

create table if not exists learning.options (
    id          uuid    primary key default gen_random_uuid(),
    question_id uuid    not null references learning.questions (id) on delete cascade,  -- hard FK
    content     text    not null,
    is_correct  boolean not null default false
);
create index if not exists options_question_idx on learning.options (question_id);

comment on column learning.options.is_correct is
    'Never serialised to students — stripped in the response schema (backend.md §12)';

-- --- Attempt history ---------------------------------------------------

create table if not exists learning.histories (
    id           uuid             primary key default gen_random_uuid(),
    user_id      uuid             not null,   -- logical FK -> account.users.id
    lesson_id    uuid             not null,   -- logical FK -> content.lessons.id
    highest_score double precision not null default 0,
    completed_at timestamptz      not null default now()
);

-- "highest_score" implies one aggregate row per (user, lesson): upsert and keep
-- the best score. Drop this constraint if you'd rather store every attempt
-- (then rename the table to "attempts" and add a per-row score).
alter table learning.histories
    drop constraint if exists histories_user_lesson_key;
alter table learning.histories
    add  constraint histories_user_lesson_key unique (user_id, lesson_id);

create index if not exists histories_user_idx on learning.histories (user_id);

-- --- Favorites --------------------------------------------------------

create table if not exists learning.favorite_lessons (
    user_id    uuid        not null,   -- logical FK -> account.users.id
    lesson_id  uuid        not null,   -- logical FK -> content.lessons.id
    created_at timestamptz not null default now(),
    primary key (user_id, lesson_id)
);
create index if not exists favorite_lessons_lesson_idx on learning.favorite_lessons (lesson_id);

-- --- Comments (threaded) --------------------------------------------

create table if not exists learning.comments (
    id         uuid        primary key default gen_random_uuid(),
    lesson_id  uuid        not null,   -- logical FK -> content.lessons.id
    user_id    uuid        not null,   -- logical FK -> account.users.id
    parent_id  uuid        references learning.comments (id) on delete cascade,  -- hard self FK
    content    text        not null,
    created_at timestamptz not null default now()
);
create index if not exists comments_lesson_idx on learning.comments (lesson_id);
create index if not exists comments_parent_idx on learning.comments (parent_id);

comment on column learning.comments.parent_id is 'Null => top-level comment; set => reply';
-- ==========================================================================
-- 04_payment.sql  —  payment service (owner: Long)
-- Bounded context M4. Checkout transactions.
--
-- Simplified per the ER diagram: no `plans` table and no `outbox` table
-- (backend.md §5 has both). If you keep the outbox pattern later, add it here.
-- ==========================================================================

set search_path = payment, public;

create table if not exists payment.transactions (
    id             uuid          primary key default gen_random_uuid(),
    user_id        uuid          not null,        -- logical FK -> account.users.id
    amount         numeric(14,2) not null check (amount >= 0),   -- VND
    payment_method text          not null
                       check (payment_method in ('VNPAY', 'MOMO')),
    status         text          not null default 'PENDING'
                       check (status in ('PENDING', 'SUCCESS', 'FAILED')),
    created_at     timestamptz   not null default now()
);

create index if not exists transactions_user_idx   on payment.transactions (user_id);
create index if not exists transactions_status_idx on payment.transactions (status);

comment on table  payment.transactions               is 'Checkout attempts. SUCCESS drives the VIP upgrade event.';
comment on column payment.transactions.payment_method is 'VNPAY | MOMO';
comment on column payment.transactions.status         is 'PENDING | SUCCESS | FAILED';
-- ==========================================================================
-- 05_notification.sql  —  notification service (owner: Dat)
-- Bounded context M2. In-app messages and per-user reminder settings.
-- ==========================================================================

set search_path = notification, public;

create table if not exists notification.messages (
    id         uuid        primary key default gen_random_uuid(),
    user_id    uuid        not null,   -- logical FK -> account.users.id
    title      text        not null,
    content    text        not null,
    is_read    boolean     not null default false,
    created_at timestamptz not null default now()
);

create index if not exists messages_user_unread_idx
    on notification.messages (user_id, created_at desc)
    where is_read = false;

create table if not exists notification.settings (
    user_id               uuid    primary key,   -- logical FK -> account.users.id
    enable_daily_reminder boolean not null default true,
    device_token          text
);

comment on table  notification.settings              is 'One row per user; created on first login or via defaults';
comment on column notification.settings.device_token is 'Expo push token for the 20:00 study reminder (mobile.md §6)';
