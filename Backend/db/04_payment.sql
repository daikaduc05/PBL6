-- ==========================================================================
-- 04_payment.sql  —  payment service (owner: Long)
-- Bounded context M4. Checkout transactions.
--
-- Simplified per the ER diagram: no `plans` table (backend.md §5 has one).
--
-- `plan_code` (added T29, Alembic migration 0002 on the live Supabase DB —
-- this file is the historical baseline, kept in sync by hand; re-running it
-- here is a no-op on an existing table since the column already exists
-- there via the migration, not via this script) stands in for the dropped
-- `plans` table — see Backend/services/payment/src/payment/plans.py for the
-- hardcoded catalogue.
--
-- `outbox` (added T31, Alembic migration 0004) IS the outbox table
-- backend.md §5 originally specified — reintroduced once the relay worker
-- actually needed it. See payment.outbox.relay.
-- ==========================================================================

set search_path = payment, public;

create table if not exists payment.transactions (
    id             uuid          primary key default gen_random_uuid(),
    user_id        uuid          not null,        -- logical FK -> account.users.id
    amount         numeric(14,2) not null check (amount >= 0),   -- VND
    payment_method text          not null
                       check (payment_method in ('VNPAY', 'MOMO')),
    plan_code      text          not null default 'VIP_1_MONTH',
    provider_txn_ref text        unique,          -- set by T30's webhook, idempotency key
    status         text          not null default 'PENDING'
                       check (status in ('PENDING', 'SUCCESS', 'FAILED')),
    created_at     timestamptz   not null default now()
);

create index if not exists transactions_user_idx   on payment.transactions (user_id);
create index if not exists transactions_status_idx on payment.transactions (status);

comment on table  payment.transactions               is 'Checkout attempts. SUCCESS drives the VIP upgrade event.';
comment on column payment.transactions.payment_method is 'VNPAY | MOMO';
comment on column payment.transactions.plan_code      is 'Key into payment.plans.PLANS — which VIP plan was purchased';
comment on column payment.transactions.provider_txn_ref is 'Gateway txn id, set on first webhook delivery — idempotency key';
comment on column payment.transactions.status         is 'PENDING | SUCCESS | FAILED';

create table if not exists payment.outbox (
    id             uuid        primary key default gen_random_uuid(),
    aggregate_id   uuid        not null,        -- payment.transactions.id
    event_type     text        not null,        -- e.g. 'payment.succeeded'
    payload        jsonb       not null,        -- envelope's `data` field (backend.md §6)
    created_at     timestamptz not null default now(),
    published_at   timestamptz                  -- null until the relay confirms delivery
);

create index if not exists outbox_unpublished_idx on payment.outbox (created_at)
    where published_at is null;

comment on table  payment.outbox            is 'Outbox pattern (T31): written in the same DB transaction as a transactions status update; relayed to RabbitMQ pbl6.events by payment.outbox.relay.';
comment on column payment.outbox.payload    is 'The envelope''s `data` field — event_id/event_type/producer/occurred_at are filled in by the relay from this row''s own id/event_type/created_at.';
comment on column payment.outbox.published_at is 'Set by the relay after a successful publish ack. Null => not yet delivered (or delivery unconfirmed) => still a candidate for the next relay tick.';
