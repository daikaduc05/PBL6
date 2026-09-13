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
