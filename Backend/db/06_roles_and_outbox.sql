-- ==========================================================================
-- 06_roles_and_outbox.sql  —  SOA Database Isolation & Outbox Tables
--
-- 1. Creates Transactional Outbox tables for `account` and `content` schemas
--    (mirroring `payment.outbox`).
-- 2. Enforces least-privilege Database-per-Service isolation at the PostgreSQL
--    role level: each microservice is granted a dedicated DB role that ONLY has
--    USAGE/CREATE/ALL privileges on its own schema and owns the tables/types
--    inside its schema (so Alembic migrations with ALTER TABLE work cleanly).
--
-- IMPORTANT: Set real passwords out-of-band via `ALTER ROLE <role> WITH PASSWORD '...'`
-- or psql variables — never commit real role passwords to Git.
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

-- 2. Dedicated PostgreSQL roles per bounded context (passwords set out-of-band)
do $$
begin
    if not exists (select 1 from pg_roles where rolname = 'pbl6_account_role') then
        create role pbl6_account_role login;
    end if;
    if not exists (select 1 from pg_roles where rolname = 'pbl6_content_role') then
        create role pbl6_content_role login;
    end if;
    if not exists (select 1 from pg_roles where rolname = 'pbl6_learning_role') then
        create role pbl6_learning_role login;
    end if;
    if not exists (select 1 from pg_roles where rolname = 'pbl6_payment_role') then
        create role pbl6_payment_role login;
    end if;
    if not exists (select 1 from pg_roles where rolname = 'pbl6_notification_role') then
        create role pbl6_notification_role login;
    end if;
end
$$;

-- Allow current admin role (postgres on Supabase) to SET ROLE / transfer ownership
grant pbl6_account_role, pbl6_content_role, pbl6_learning_role, pbl6_payment_role, pbl6_notification_role to current_user;

-- 3. Revoke cross-schema access from PUBLIC and grant each role access ONLY to its own schema
revoke all on schema account, content, learning, payment, notification from public;

grant usage, create on schema account to pbl6_account_role;
grant all privileges on all tables in schema account to pbl6_account_role;
grant all privileges on all sequences in schema account to pbl6_account_role;
alter default privileges in schema account grant all on tables to pbl6_account_role;
alter default privileges in schema account grant all on sequences to pbl6_account_role;

grant usage, create on schema content to pbl6_content_role;
grant all privileges on all tables in schema content to pbl6_content_role;
grant all privileges on all sequences in schema content to pbl6_content_role;
alter default privileges in schema content grant all on tables to pbl6_content_role;
alter default privileges in schema content grant all on sequences to pbl6_content_role;

grant usage, create on schema learning to pbl6_learning_role;
grant all privileges on all tables in schema learning to pbl6_learning_role;
grant all privileges on all sequences in schema learning to pbl6_learning_role;
alter default privileges in schema learning grant all on tables to pbl6_learning_role;
alter default privileges in schema learning grant all on sequences to pbl6_learning_role;

grant usage, create on schema payment to pbl6_payment_role;
grant all privileges on all tables in schema payment to pbl6_payment_role;
grant all privileges on all sequences in schema payment to pbl6_payment_role;
alter default privileges in schema payment grant all on tables to pbl6_payment_role;
alter default privileges in schema payment grant all on sequences to pbl6_payment_role;

grant usage, create on schema notification to pbl6_notification_role;
grant all privileges on all tables in schema notification to pbl6_notification_role;
grant all privileges on all sequences in schema notification to pbl6_notification_role;
alter default privileges in schema notification grant all on tables to pbl6_notification_role;
alter default privileges in schema notification grant all on sequences to pbl6_notification_role;

-- 4. Transfer ownership of existing tables, sequences, and views in each schema
--    to its dedicated role so service-scoped Alembic migrations (ALTER TABLE) succeed.
do $$
declare
    rec record;
    mapping jsonb := '{
        "account": "pbl6_account_role",
        "content": "pbl6_content_role",
        "learning": "pbl6_learning_role",
        "payment": "pbl6_payment_role",
        "notification": "pbl6_notification_role"
    }'::jsonb;
    s_name text;
    r_name text;
begin
    for s_name, r_name in select key, value #>> '{}' from jsonb_each(mapping) loop
        execute format('alter schema %I owner to %I', s_name, r_name);

        for rec in
            select tablename from pg_tables where schemaname = s_name
        loop
            execute format('alter table %I.%I owner to %I', s_name, rec.tablename, r_name);
        end loop;

        for rec in
            select sequencename from pg_sequences where schemaname = s_name
        loop
            execute format('alter sequence %I.%I owner to %I', s_name, rec.sequencename, r_name);
        end loop;
    end loop;
end
$$;
