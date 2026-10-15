-- ==========================================================================
-- 06_notification_processed_events.sql  —  notification service (owner: Dat)
-- Bounded context M2, additive migration. Run AFTER 05_notification.sql.
--
-- Why this table exists
-- --------------------
-- The payment service publishes payment.succeeded through an outbox relay,
-- which is at-least-once by design: a crash between "publish" and "ack" makes
-- RabbitMQ redeliver the same message. Without a dedupe record the consumer
-- would insert a second "VIP activated" row into notification.messages and the
-- user would see the same notification twice.
--
-- The consumer inserts (event_id) inside the same transaction that writes the
-- message. A duplicate delivery hits the primary key, the transaction rolls
-- back, and the message is acked without side effects.
-- ==========================================================================

set search_path = notification, public;

create table if not exists notification.processed_events (
    event_id     uuid        primary key,   -- envelope.event_id from pbl6.events
    event_type   text        not null,      -- kept for debugging / DLQ triage
    processed_at timestamptz not null default now()
);

create index if not exists processed_events_processed_at_idx
    on notification.processed_events (processed_at);

comment on table  notification.processed_events            is
    'Idempotency ledger for RabbitMQ consumers. One row per successfully handled event.';
comment on column notification.processed_events.event_id   is
    'Primary key = the dedupe mechanism. Insert conflict means "already handled, ack and skip".';
comment on column notification.processed_events.processed_at is
    'Rows older than ~30 days can be pruned; redelivery windows are minutes, not weeks.';
