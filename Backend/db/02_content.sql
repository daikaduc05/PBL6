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
