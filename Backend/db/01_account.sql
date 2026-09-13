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
