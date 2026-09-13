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
