-- ============================================
-- PBL6 DATABASE SCHEMA
-- PostgreSQL
-- ============================================

-- =========================
-- ACCOUNT
-- =========================

CREATE TABLE account_users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,

    role VARCHAR(20) NOT NULL DEFAULT 'CUSTOMER'
        CHECK (role IN ('CUSTOMER', 'EDITOR', 'ADMIN')),

    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE', 'INACTIVE', 'LOCKED')),

    is_vip BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- =========================
-- CONTENT
-- =========================

CREATE TABLE content_categories (
    category_id SERIAL PRIMARY KEY,

    name VARCHAR(100) NOT NULL UNIQUE,

    description TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE content_lessons (
    lesson_id SERIAL PRIMARY KEY,

    category_id INTEGER NOT NULL,

    title VARCHAR(200) NOT NULL,

    description TEXT,

    content TEXT,

    level VARCHAR(20) NOT NULL DEFAULT 'EASY'
        CHECK (level IN ('EASY', 'MEDIUM', 'HARD')),

    is_free BOOLEAN NOT NULL DEFAULT TRUE,

    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT'
        CHECK (status IN ('DRAFT', 'PUBLISHED')),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_lesson_category
        FOREIGN KEY (category_id)
        REFERENCES content_categories(category_id)
        ON DELETE CASCADE
);


-- =========================
-- LEARNING
-- =========================

CREATE TABLE learning_quizzes (
    quiz_id SERIAL PRIMARY KEY,

    lesson_id INTEGER NOT NULL,

    title VARCHAR(200) NOT NULL,

    description TEXT,

    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT'
        CHECK (status IN ('DRAFT', 'PUBLISHED')),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_quiz_lesson
        FOREIGN KEY (lesson_id)
        REFERENCES content_lessons(lesson_id)
        ON DELETE CASCADE
);


CREATE TABLE learning_questions (
    question_id SERIAL PRIMARY KEY,

    quiz_id INTEGER NOT NULL,

    question_text TEXT NOT NULL,

    question_type VARCHAR(30) DEFAULT 'MULTIPLE_CHOICE',

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_question_quiz
        FOREIGN KEY (quiz_id)
        REFERENCES learning_quizzes(quiz_id)
        ON DELETE CASCADE
);


CREATE TABLE learning_options (
    option_id SERIAL PRIMARY KEY,

    question_id INTEGER NOT NULL,

    option_text TEXT NOT NULL,

    is_correct BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT fk_option_question
        FOREIGN KEY (question_id)
        REFERENCES learning_questions(question_id)
        ON DELETE CASCADE
);


CREATE TABLE learning_history (
    history_id SERIAL PRIMARY KEY,

    user_id INTEGER NOT NULL,

    quiz_id INTEGER NOT NULL,

    score NUMERIC(5,2),

    completed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_history_user
        FOREIGN KEY (user_id)
        REFERENCES account_users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_history_quiz
        FOREIGN KEY (quiz_id)
        REFERENCES learning_quizzes(quiz_id)
        ON DELETE CASCADE
);


CREATE TABLE learning_favorites (
    favorite_id SERIAL PRIMARY KEY,

    user_id INTEGER NOT NULL,

    lesson_id INTEGER NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_favorite_user
        FOREIGN KEY (user_id)
        REFERENCES account_users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_favorite_lesson
        FOREIGN KEY (lesson_id)
        REFERENCES content_lessons(lesson_id)
        ON DELETE CASCADE,

    CONSTRAINT unique_user_lesson
        UNIQUE (user_id, lesson_id)
);


CREATE TABLE learning_comments (
    comment_id SERIAL PRIMARY KEY,

    user_id INTEGER NOT NULL,

    lesson_id INTEGER NOT NULL,

    comment_text TEXT NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_comment_user
        FOREIGN KEY (user_id)
        REFERENCES account_users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_comment_lesson
        FOREIGN KEY (lesson_id)
        REFERENCES content_lessons(lesson_id)
        ON DELETE CASCADE
);


-- =========================
-- PAYMENT
-- =========================

CREATE TABLE payment_transactions (
    transaction_id SERIAL PRIMARY KEY,

    user_id INTEGER NOT NULL,

    amount NUMERIC(10,2) NOT NULL,

    payment_plan VARCHAR(100) NOT NULL,

    transaction_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'SUCCESS', 'FAILED')),

    CONSTRAINT fk_transaction_user
        FOREIGN KEY (user_id)
        REFERENCES account_users(user_id)
        ON DELETE CASCADE
);


-- =========================
-- NOTIFICATION
-- =========================

CREATE TABLE notification_messages (
    notification_id SERIAL PRIMARY KEY,

    user_id INTEGER,

    title VARCHAR(200) NOT NULL,

    message TEXT NOT NULL,

    type VARCHAR(30) NOT NULL
        CHECK (type IN ('LESSON', 'QUIZ', 'PAYMENT', 'SYSTEM')),

    status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'SENT')),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_notification_user
        FOREIGN KEY (user_id)
        REFERENCES account_users(user_id)
        ON DELETE CASCADE
);


CREATE TABLE notification_settings (
    setting_id SERIAL PRIMARY KEY,

    user_id INTEGER NOT NULL UNIQUE,

    daily_reminder BOOLEAN NOT NULL DEFAULT TRUE,

    device_token TEXT,

    CONSTRAINT fk_setting_user
        FOREIGN KEY (user_id)
        REFERENCES account_users(user_id)
        ON DELETE CASCADE
);