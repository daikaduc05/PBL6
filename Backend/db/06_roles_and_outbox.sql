-- ==========================================================================
-- 06_roles_and_outbox.sql  —  SOA Database Isolation & Outbox Tables
--
-- 1. Creates Transactional Outbox tables for `account` and `content` schemas
--    (mirroring `payment.outbox`).
-- 2. Enforces least-privilege Database-per-Service isolation at the PostgreSQL
--    role level: each microservice is granted a dedicated DB role that ONLY has
--    USAGE/ALL privileges on its own schema and is explicitly denied access to
--    other services' schemas.
-- ==========================================================================

-- 1. Outbox tables for Account and Content services
create table if not exists account.outbox (
    id           uuid primary key default gen_random_uuid(),
    aggregate_id uuid not null,
    event_type   text not null,
    payload      jsonb not null,
    created_at   timestamptz not null default now(),
    published_at timestamptz
);

create index if not exists account_outbox_unpublished_idx
    on account.outbox (created_at)
    where published_at is null;

create table if not exists content.outbox (
    id           uuid primary key default gen_random_uuid(),
    aggregate_id uuid not null,
    event_type   text not null,
    payload      jsonb not null,
    created_at   timestamptz not null default now(),
    published_at timestamptz
);

create index if not exists content_outbox_unpublished_idx
    on content.outbox (created_at)
    where published_at is null;

-- 2. Dedicated PostgreSQL roles per bounded context (Database-per-Service isolation)
do $$
begin
    if not exists (select 1 from pg_roles where rolname = 'pbl6_account_role') then
        create role pbl6_account_role login password 'change_me_account';
    end if;
    if not exists (select 1 from pg_roles where rolname = 'pbl6_content_role') then
        create role pbl6_content_role login password 'change_me_content';
    end if;
    if not exists (select 1 from pg_roles where rolname = 'pbl6_learning_role') then
        create role pbl6_learning_role login password 'change_me_learning';
    end if;
    if not exists (select 1 from pg_roles where rolname = 'pbl6_payment_role') then
        create role pbl6_payment_role login password 'change_me_payment';
    end if;
    if not exists (select 1 from pg_roles where rolname = 'pbl6_notification_role') then
        create role pbl6_notification_role login password 'change_me_notification';
    end if;
end
$$;

-- Revoke cross-schema access and grant each role permissions ONLY on its own schema
revoke all on schema account, content, learning, payment, notification from public;

grant usage, create on schema account to pbl6_account_role;
grant all privileges on all tables in schema account to pbl6_account_role;
alter default privileges in schema account grant all on tables to pbl6_account_role;

grant usage, create on schema content to pbl6_content_role;
grant all privileges on all tables in schema content to pbl6_content_role;
alter default privileges in schema content grant all on tables to pbl6_content_role;

grant usage, create on schema learning to pbl6_learning_role;
grant all privileges on all tables in schema learning to pbl6_learning_role;
alter default privileges in schema learning grant all on tables to pbl6_learning_role;

grant usage, create on schema payment to pbl6_payment_role;
grant all privileges on all tables in schema payment to pbl6_payment_role;
alter default privileges in schema payment grant all on tables to pbl6_payment_role;

grant usage, create on schema notification to pbl6_notification_role;
grant all privileges on all tables in schema notification to pbl6_notification_role;
alter default privileges in schema notification grant all on tables to pbl6_notification_role;

