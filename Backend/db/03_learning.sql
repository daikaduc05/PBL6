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
