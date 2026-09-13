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
