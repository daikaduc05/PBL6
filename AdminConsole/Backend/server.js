const express = require("express");
const cors = require("cors");
const dotenv = require("dotenv");
const bcrypt = require("bcrypt");
const pool = require("./db");

dotenv.config();

const app = express();
const PORT = 5000;

app.use(cors());
app.use(express.json());


// ========================================
// HOME
// ========================================

app.get("/", (req, res) => {
  res.json({
    success: true,
    message: "PBL6 Backend API is running!",
  });
});


// ========================================
// TEST DATABASE
// ========================================

app.get("/api/test-db", async (req, res) => {
  try {
    const result = await pool.query("SELECT NOW()");

    res.json({
      success: true,
      message: "PostgreSQL connected successfully!",
      time: result.rows[0].now,
    });
  } catch (error) {
    console.error("Database error:", error);

    res.status(500).json({
      success: false,
      message: "Database connection failed",
      error: error.message,
    });
  }
});


// ========================================
// USERS
// ========================================

// GET ALL USERS
app.get("/api/users", async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT
        user_id,
        username,
        email,
        role,
        status,
        is_vip,
        created_at
      FROM account_users
      ORDER BY user_id
    `);

    res.json({
      success: true,
      users: result.rows,
    });
  } catch (error) {
    console.error("Get users error:", error);

    res.status(500).json({
      success: false,
      message: "Failed to get users",
      error: error.message,
    });
  }
});


// GET USER BY ID
app.get("/api/users/:id", async (req, res) => {
  try {
    const { id } = req.params;

    const result = await pool.query(
      `
      SELECT
        user_id,
        username,
        email,
        role,
        status,
        is_vip,
        created_at
      FROM account_users
      WHERE user_id = $1
      `,
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: "User not found",
      });
    }

    res.json({
      success: true,
      user: result.rows[0],
    });
  } catch (error) {
    console.error("Get user error:", error);

    res.status(500).json({
      success: false,
      message: "Failed to get user",
      error: error.message,
    });
  }
});


// CREATE USER
app.post("/api/users", async (req, res) => {
  try {
    const {
      username,
      email,
      password,
      role,
      status,
      is_vip,
    } = req.body;

    if (!username || !email || !password) {
      return res.status(400).json({
        success: false,
        message: "username, email and password are required",
      });
    }

    const existingUser = await pool.query(
      `
      SELECT user_id
      FROM account_users
      WHERE username = $1 OR email = $2
      `,
      [username, email]
    );

    if (existingUser.rows.length > 0) {
      return res.status(409).json({
        success: false,
        message: "Username or email already exists",
      });
    }

    const password_hash = await bcrypt.hash(password, 10);

    const result = await pool.query(
      `
      INSERT INTO account_users
      (
        username,
        email,
        password_hash,
        role,
        status,
        is_vip
      )
      VALUES ($1, $2, $3, $4, $5, $6)
      RETURNING
        user_id,
        username,
        email,
        role,
        status,
        is_vip,
        created_at
      `,
      [
        username,
        email,
        password_hash,
        role || "CUSTOMER",
        status || "ACTIVE",
        is_vip || false,
      ]
    );

    res.status(201).json({
      success: true,
      message: "User created successfully!",
      user: result.rows[0],
    });
  } catch (error) {
    console.error("Create user error:", error);

    res.status(500).json({
      success: false,
      message: "Failed to create user",
      error: error.message,
    });
  }
});


// UPDATE USER
app.put("/api/users/:id", async (req, res) => {
  try {
    const { id } = req.params;

    const {
      username,
      email,
      role,
      status,
      is_vip,
    } = req.body;

    if (!username || !email) {
      return res.status(400).json({
        success: false,
        message: "username and email are required",
      });
    }

    const existingUser = await pool.query(
      `
      SELECT user_id
      FROM account_users
      WHERE (username = $1 OR email = $2)
      AND user_id <> $3
      `,
      [username, email, id]
    );

    if (existingUser.rows.length > 0) {
      return res.status(409).json({
        success: false,
        message: "Username or email already exists",
      });
    }

    const result = await pool.query(
      `
      UPDATE account_users
      SET
        username = $1,
        email = $2,
        role = $3,
        status = $4,
        is_vip = $5
      WHERE user_id = $6
      RETURNING
        user_id,
        username,
        email,
        role,
        status,
        is_vip,
        created_at
      `,
      [
        username,
        email,
        role || "CUSTOMER",
        status || "ACTIVE",
        is_vip || false,
        id,
      ]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: "User not found",
      });
    }

    res.json({
      success: true,
      message: "User updated successfully!",
      user: result.rows[0],
    });
  } catch (error) {
    console.error("Update user error:", error);

    res.status(500).json({
      success: false,
      message: "Failed to update user",
      error: error.message,
    });
  }
});


// DELETE USER
app.delete("/api/users/:id", async (req, res) => {
  try {
    const { id } = req.params;

    const result = await pool.query(
      `
      DELETE FROM account_users
      WHERE user_id = $1
      RETURNING user_id, username, email
      `,
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: "User not found",
      });
    }

    res.json({
      success: true,
      message: "User deleted successfully!",
      user: result.rows[0],
    });
  } catch (error) {
    console.error("Delete user error:", error);

    res.status(500).json({
      success: false,
      message: "Failed to delete user",
      error: error.message,
    });
  }
});


// ========================================
// CATEGORIES
// ========================================

// GET ALL CATEGORIES
app.get("/api/categories", async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT
        category_id,
        name,
        description,
        created_at
      FROM content_categories
      ORDER BY category_id
    `);

    res.json({
      success: true,
      categories: result.rows,
    });
  } catch (error) {
    console.error("Get categories error:", error);

    res.status(500).json({
      success: false,
      message: "Failed to get categories",
      error: error.message,
    });
  }
});


// GET CATEGORY BY ID
app.get("/api/categories/:id", async (req, res) => {
  try {
    const { id } = req.params;

    const result = await pool.query(
      `
      SELECT
        category_id,
        name,
        description,
        created_at
      FROM content_categories
      WHERE category_id = $1
      `,
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: "Category not found",
      });
    }

    res.json({
      success: true,
      category: result.rows[0],
    });
  } catch (error) {
    console.error("Get category error:", error);

    res.status(500).json({
      success: false,
      message: "Failed to get category",
      error: error.message,
    });
  }
});


// CREATE CATEGORY
app.post("/api/categories", async (req, res) => {
  try {
    const { name, description } = req.body;

    if (!name || name.trim() === "") {
      return res.status(400).json({
        success: false,
        message: "Category name is required",
      });
    }

    const existingCategory = await pool.query(
      `
      SELECT category_id
      FROM content_categories
      WHERE LOWER(name) = LOWER($1)
      `,
      [name.trim()]
    );

    if (existingCategory.rows.length > 0) {
      return res.status(409).json({
        success: false,
        message: "Category name already exists",
      });
    }

    const result = await pool.query(
      `
      INSERT INTO content_categories
      (
        name,
        description
      )
      VALUES ($1, $2)
      RETURNING
        category_id,
        name,
        description,
        created_at
      `,
      [
        name.trim(),
        description ? description.trim() : null,
      ]
    );

    res.status(201).json({
      success: true,
      message: "Category created successfully!",
      category: result.rows[0],
    });
  } catch (error) {
    console.error("Create category error:", error);

    res.status(500).json({
      success: false,
      message: "Failed to create category",
      error: error.message,
    });
  }
});


// UPDATE CATEGORY
app.put("/api/categories/:id", async (req, res) => {
  try {
    const { id } = req.params;
    const { name, description } = req.body;

    if (!name || name.trim() === "") {
      return res.status(400).json({
        success: false,
        message: "Category name is required",
      });
    }

    const existingCategory = await pool.query(
      `
      SELECT category_id
      FROM content_categories
      WHERE LOWER(name) = LOWER($1)
      AND category_id <> $2
      `,
      [name.trim(), id]
    );

    if (existingCategory.rows.length > 0) {
      return res.status(409).json({
        success: false,
        message: "Category name already exists",
      });
    }

    const result = await pool.query(
      `
      UPDATE content_categories
      SET
        name = $1,
        description = $2
      WHERE category_id = $3
      RETURNING
        category_id,
        name,
        description,
        created_at
      `,
      [
        name.trim(),
        description ? description.trim() : null,
        id,
      ]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: "Category not found",
      });
    }

    res.json({
      success: true,
      message: "Category updated successfully!",
      category: result.rows[0],
    });
  } catch (error) {
    console.error("Update category error:", error);

    res.status(500).json({
      success: false,
      message: "Failed to update category",
      error: error.message,
    });
  }
});


// DELETE CATEGORY
app.delete("/api/categories/:id", async (req, res) => {
  try {
    const { id } = req.params;

    const result = await pool.query(
      `
      DELETE FROM content_categories
      WHERE category_id = $1
      RETURNING
        category_id,
        name,
        description
      `,
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: "Category not found",
      });
    }

    res.json({
      success: true,
      message: "Category deleted successfully!",
      category: result.rows[0],
    });
  } catch (error) {
    console.error("Delete category error:", error);

    if (error.code === "23503") {
      return res.status(400).json({
        success: false,
        message:
          "Cannot delete this category because it is being used by lessons",
      });
    }

    res.status(500).json({
      success: false,
      message: "Failed to delete category",
      error: error.message,
    });
  }
});


// ========================================
// LESSONS
// ========================================

// GET ALL LESSONS
app.get("/api/lessons", async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT
        l.lesson_id,
        l.category_id,
        c.name AS category_name,
        l.title,
        l.description,
        l.content,
        l.level,
        l.is_free,
        l.status,
        l.created_at,
        l.updated_at
      FROM content_lessons l
      LEFT JOIN content_categories c
        ON l.category_id = c.category_id
      ORDER BY l.lesson_id
    `);

    res.json({
      success: true,
      lessons: result.rows,
    });
  } catch (error) {
    console.error("Get lessons error:", error);

    res.status(500).json({
      success: false,
      message: "Failed to get lessons",
      error: error.message,
    });
  }
});


// GET LESSON BY ID
app.get("/api/lessons/:id", async (req, res) => {
  try {
    const { id } = req.params;

    const result = await pool.query(
      `
      SELECT
        l.lesson_id,
        l.category_id,
        c.name AS category_name,
        l.title,
        l.description,
        l.content,
        l.level,
        l.is_free,
        l.status,
        l.created_at,
        l.updated_at
      FROM content_lessons l
      LEFT JOIN content_categories c
        ON l.category_id = c.category_id
      WHERE l.lesson_id = $1
      `,
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: "Lesson not found",
      });
    }

    res.json({
      success: true,
      lesson: result.rows[0],
    });
  } catch (error) {
    console.error("Get lesson error:", error);

    res.status(500).json({
      success: false,
      message: "Failed to get lesson",
      error: error.message,
    });
  }
});


// CREATE LESSON
app.post("/api/lessons", async (req, res) => {
  try {
    const {
      category_id,
      title,
      description,
      content,
      level,
      is_free,
      status,
    } = req.body;

    if (!category_id || !title || title.trim() === "") {
      return res.status(400).json({
        success: false,
        message: "category_id and title are required",
      });
    }

    const category = await pool.query(
      `
      SELECT category_id
      FROM content_categories
      WHERE category_id = $1
      `,
      [category_id]
    );

    if (category.rows.length === 0) {
      return res.status(400).json({
        success: false,
        message: "Category not found",
      });
    }

    const result = await pool.query(
      `
      INSERT INTO content_lessons
      (
        category_id,
        title,
        description,
        content,
        level,
        is_free,
        status,
        created_at,
        updated_at
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
      RETURNING
        lesson_id,
        category_id,
        title,
        description,
        content,
        level,
        is_free,
        status,
        created_at,
        updated_at
      `,
      [
        category_id,
        title.trim(),
        description ? description.trim() : null,
        content ? content.trim() : null,
        level || "EASY",
        is_free !== undefined ? is_free : true,
        status || "DRAFT",
      ]
    );

    res.status(201).json({
      success: true,
      message: "Lesson created successfully!",
      lesson: result.rows[0],
    });
  } catch (error) {
    console.error("Create lesson error:", error);

    res.status(500).json({
      success: false,
      message: "Failed to create lesson",
      error: error.message,
    });
  }
});


// UPDATE LESSON
app.put("/api/lessons/:id", async (req, res) => {
  try {
    const { id } = req.params;

    const {
      category_id,
      title,
      description,
      content,
      level,
      is_free,
      status,
    } = req.body;

    if (!category_id || !title || title.trim() === "") {
      return res.status(400).json({
        success: false,
        message: "category_id and title are required",
      });
    }

    const category = await pool.query(
      `
      SELECT category_id
      FROM content_categories
      WHERE category_id = $1
      `,
      [category_id]
    );

    if (category.rows.length === 0) {
      return res.status(400).json({
        success: false,
        message: "Category not found",
      });
    }

    const result = await pool.query(
      `
      UPDATE content_lessons
      SET
        category_id = $1,
        title = $2,
        description = $3,
        content = $4,
        level = $5,
        is_free = $6,
        status = $7,
        updated_at = NOW()
      WHERE lesson_id = $8
      RETURNING
        lesson_id,
        category_id,
        title,
        description,
        content,
        level,
        is_free,
        status,
        created_at,
        updated_at
      `,
      [
        category_id,
        title.trim(),
        description ? description.trim() : null,
        content ? content.trim() : null,
        level || "EASY",
        is_free !== undefined ? is_free : true,
        status || "DRAFT",
        id,
      ]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: "Lesson not found",
      });
    }

    res.json({
      success: true,
      message: "Lesson updated successfully!",
      lesson: result.rows[0],
    });
  } catch (error) {
    console.error("Update lesson error:", error);

    res.status(500).json({
      success: false,
      message: "Failed to update lesson",
      error: error.message,
    });
  }
});


// DELETE LESSON
app.delete("/api/lessons/:id", async (req, res) => {
  try {
    const { id } = req.params;

    const result = await pool.query(
      `
      DELETE FROM content_lessons
      WHERE lesson_id = $1
      RETURNING
        lesson_id,
        title
      `,
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: "Lesson not found",
      });
    }

    res.json({
      success: true,
      message: "Lesson deleted successfully!",
      lesson: result.rows[0],
    });
  } catch (error) {
    console.error("Delete lesson error:", error);

    if (error.code === "23503") {
      return res.status(400).json({
        success: false,
        message:
          "Cannot delete this lesson because it is being used by quizzes or other data",
      });
    }

    res.status(500).json({
      success: false,
      message: "Failed to delete lesson",
      error: error.message,
    });
  }
});


// ========================================
// QUIZZES
// ========================================

// GET ALL QUIZZES
app.get("/api/quizzes", async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT
        q.quiz_id,
        q.lesson_id,
        l.title AS lesson_title,
        q.title,
        q.description,
        q.status,
        q.created_at
      FROM learning_quizzes q
      LEFT JOIN content_lessons l
        ON q.lesson_id = l.lesson_id
      ORDER BY q.quiz_id
    `);

    res.json({
      success: true,
      quizzes: result.rows,
    });
  } catch (error) {
    console.error("Get quizzes error:", error);

    res.status(500).json({
      success: false,
      message: "Failed to get quizzes",
      error: error.message,
    });
  }
});


// GET QUIZ BY ID
app.get("/api/quizzes/:id", async (req, res) => {
  try {
    const { id } = req.params;

    const result = await pool.query(
      `
      SELECT
        q.quiz_id,
        q.lesson_id,
        l.title AS lesson_title,
        q.title,
        q.description,
        q.status,
        q.created_at
      FROM learning_quizzes q
      LEFT JOIN content_lessons l
        ON q.lesson_id = l.lesson_id
      WHERE q.quiz_id = $1
      `,
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: "Quiz not found",
      });
    }

    res.json({
      success: true,
      quiz: result.rows[0],
    });
  } catch (error) {
    console.error("Get quiz error:", error);

    res.status(500).json({
      success: false,
      message: "Failed to get quiz",
      error: error.message,
    });
  }
});


// CREATE QUIZ
app.post("/api/quizzes", async (req, res) => {
  try {
    const {
      lesson_id,
      title,
      description,
      status,
    } = req.body;

    if (!lesson_id || !title || title.trim() === "") {
      return res.status(400).json({
        success: false,
        message: "lesson_id and title are required",
      });
    }

    const lesson = await pool.query(
      `
      SELECT lesson_id
      FROM content_lessons
      WHERE lesson_id = $1
      `,
      [lesson_id]
    );

    if (lesson.rows.length === 0) {
      return res.status(400).json({
        success: false,
        message: "Lesson not found",
      });
    }

    const result = await pool.query(
      `
      INSERT INTO learning_quizzes
      (
        lesson_id,
        title,
        description,
        status,
        created_at
      )
      VALUES ($1, $2, $3, $4, NOW())
      RETURNING
        quiz_id,
        lesson_id,
        title,
        description,
        status,
        created_at
      `,
      [
        lesson_id,
        title.trim(),
        description ? description.trim() : null,
        status || "DRAFT",
      ]
    );

    res.status(201).json({
      success: true,
      message: "Quiz created successfully!",
      quiz: result.rows[0],
    });
  } catch (error) {
    console.error("Create quiz error:", error);

    res.status(500).json({
      success: false,
      message: "Failed to create quiz",
      error: error.message,
    });
  }
});


// UPDATE QUIZ
app.put("/api/quizzes/:id", async (req, res) => {
  try {
    const { id } = req.params;

    const {
      lesson_id,
      title,
      description,
      status,
    } = req.body;

    if (!lesson_id || !title || title.trim() === "") {
      return res.status(400).json({
        success: false,
        message: "lesson_id and title are required",
      });
    }

    const lesson = await pool.query(
      `
      SELECT lesson_id
      FROM content_lessons
      WHERE lesson_id = $1
      `,
      [lesson_id]
    );

    if (lesson.rows.length === 0) {
      return res.status(400).json({
        success: false,
        message: "Lesson not found",
      });
    }

    const result = await pool.query(
      `
      UPDATE learning_quizzes
      SET
        lesson_id = $1,
        title = $2,
        description = $3,
        status = $4
      WHERE quiz_id = $5
      RETURNING
        quiz_id,
        lesson_id,
        title,
        description,
        status,
        created_at
      `,
      [
        lesson_id,
        title.trim(),
        description ? description.trim() : null,
        status || "DRAFT",
        id,
      ]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: "Quiz not found",
      });
    }

    res.json({
      success: true,
      message: "Quiz updated successfully!",
      quiz: result.rows[0],
    });
  } catch (error) {
    console.error("Update quiz error:", error);

    res.status(500).json({
      success: false,
      message: "Failed to update quiz",
      error: error.message,
    });
  }
});


// DELETE QUIZ
app.delete("/api/quizzes/:id", async (req, res) => {
  try {
    const { id } = req.params;

    const result = await pool.query(
      `
      DELETE FROM learning_quizzes
      WHERE quiz_id = $1
      RETURNING
        quiz_id,
        title
      `,
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: "Quiz not found",
      });
    }

    res.json({
      success: true,
      message: "Quiz deleted successfully!",
      quiz: result.rows[0],
    });
  } catch (error) {
    console.error("Delete quiz error:", error);

    if (error.code === "23503") {
      return res.status(400).json({
        success: false,
        message:
          "Cannot delete this quiz because it is being used by questions or other data",
      });
    }

    res.status(500).json({
      success: false,
      message: "Failed to delete quiz",
      error: error.message,
    });
  }
});



// ========================================
// QUESTIONS API
// ========================================

// GET ALL QUESTIONS
app.get("/api/questions", async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT
        q.question_id,
        q.quiz_id,
        z.title AS quiz_title,
        q.question_text,
        q.question_type
      FROM learning_questions q
      LEFT JOIN learning_quizzes z
        ON q.quiz_id = z.quiz_id
      ORDER BY q.question_id
    `);

    res.json({
      success: true,
      questions: result.rows,
    });
  } catch (error) {
    console.error("Get questions error:", error);

    res.status(500).json({
      success: false,
      message: "Failed to get questions",
      error: error.message,
    });
  }
});


// GET QUESTION BY ID
app.get("/api/questions/:id", async (req, res) => {
  try {
    const { id } = req.params;

    const result = await pool.query(`
      SELECT
        q.question_id,
        q.quiz_id,
        z.title AS quiz_title,
        q.question_text,
        q.question_type
      FROM learning_questions q
      LEFT JOIN learning_quizzes z
        ON q.quiz_id = z.quiz_id
      WHERE q.question_id = $1
    `, [id]);

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: "Question not found",
      });
    }

    res.json({
      success: true,
      question: result.rows[0],
    });
  } catch (error) {
    console.error("Get question error:", error);

    res.status(500).json({
      success: false,
      message: "Failed to get question",
      error: error.message,
    });
  }
});


// CREATE QUESTION
app.post("/api/questions", async (req, res) => {
  try {
    const {
      quiz_id,
      question_text,
      question_type,
    } = req.body;

    if (!quiz_id || !question_text || !question_text.trim()) {
      return res.status(400).json({
        success: false,
        message: "Quiz and question text are required",
      });
    }

    const quizCheck = await pool.query(
      `SELECT quiz_id FROM learning_quizzes WHERE quiz_id = $1`,
      [quiz_id]
    );

    if (quizCheck.rows.length === 0) {
      return res.status(400).json({
        success: false,
        message: "Quiz not found",
      });
    }

    const result = await pool.query(
      `
      INSERT INTO learning_questions
        (quiz_id, question_text, question_type)
      VALUES
        ($1, $2, $3)
      RETURNING
        question_id,
        quiz_id,
        question_text,
        question_type
      `,
      [
        quiz_id,
        question_text.trim(),
        question_type || "MULTIPLE_CHOICE",
      ]
    );

    res.status(201).json({
      success: true,
      message: "Question created successfully!",
      question: result.rows[0],
    });
  } catch (error) {
    console.error("Create question error:", error);

    res.status(500).json({
      success: false,
      message: "Failed to create question",
      error: error.message,
    });
  }
});


// UPDATE QUESTION
app.put("/api/questions/:id", async (req, res) => {
  try {
    const { id } = req.params;

    const {
      quiz_id,
      question_text,
      question_type,
    } = req.body;

    if (!quiz_id || !question_text || !question_text.trim()) {
      return res.status(400).json({
        success: false,
        message: "Quiz and question text are required",
      });
    }

    const quizCheck = await pool.query(
      `SELECT quiz_id FROM learning_quizzes WHERE quiz_id = $1`,
      [quiz_id]
    );

    if (quizCheck.rows.length === 0) {
      return res.status(400).json({
        success: false,
        message: "Quiz not found",
      });
    }

    const result = await pool.query(
      `
      UPDATE learning_questions
      SET
        quiz_id = $1,
        question_text = $2,
        question_type = $3
      WHERE question_id = $4
      RETURNING
        question_id,
        quiz_id,
        question_text,
        question_type
      `,
      [
        quiz_id,
        question_text.trim(),
        question_type || "MULTIPLE_CHOICE",
        id,
      ]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: "Question not found",
      });
    }

    res.json({
      success: true,
      message: "Question updated successfully!",
      question: result.rows[0],
    });
  } catch (error) {
    console.error("Update question error:", error);

    res.status(500).json({
      success: false,
      message: "Failed to update question",
      error: error.message,
    });
  }
});


// DELETE QUESTION
app.delete("/api/questions/:id", async (req, res) => {
  try {
    const { id } = req.params;

    const result = await pool.query(
      `
      DELETE FROM learning_questions
      WHERE question_id = $1
      RETURNING question_id, question_text
      `,
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: "Question not found",
      });
    }

    res.json({
      success: true,
      message: "Question deleted successfully!",
      question: result.rows[0],
    });
  } catch (error) {
    console.error("Delete question error:", error);

    if (error.code === "23503") {
      return res.status(400).json({
        success: false,
        message:
          "Cannot delete this question because it is being used by options or other data",
      });
    }

    res.status(500).json({
      success: false,
      message: "Failed to delete question",
      error: error.message,
    });
  }
});


// ========================================
// OPTIONS API
// ========================================

// GET ALL OPTIONS
app.get("/api/options", async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT
        o.option_id,
        o.question_id,
        q.question_text,
        o.option_text,
        o.is_correct
      FROM learning_options o
      LEFT JOIN learning_questions q
        ON o.question_id = q.question_id
      ORDER BY o.option_id
    `);

    res.json({
      success: true,
      options: result.rows,
    });
  } catch (error) {
    console.error("Get options error:", error);

    res.status(500).json({
      success: false,
      message: "Failed to get options",
      error: error.message,
    });
  }
});


// GET OPTIONS BY QUESTION
app.get("/api/questions/:id/options", async (req, res) => {
  try {
    const { id } = req.params;

    const result = await pool.query(`
      SELECT
        option_id,
        question_id,
        option_text,
        is_correct
      FROM learning_options
      WHERE question_id = $1
      ORDER BY option_id
    `, [id]);

    res.json({
      success: true,
      options: result.rows,
    });
  } catch (error) {
    console.error("Get question options error:", error);

    res.status(500).json({
      success: false,
      message: "Failed to get options",
      error: error.message,
    });
  }
});


// CREATE OPTION
app.post("/api/options", async (req, res) => {
  try {
    const {
      question_id,
      option_text,
      is_correct,
    } = req.body;

    if (!question_id || !option_text || !option_text.trim()) {
      return res.status(400).json({
        success: false,
        message: "Question and option text are required",
      });
    }

    const questionCheck = await pool.query(
      `SELECT question_id FROM learning_questions WHERE question_id = $1`,
      [question_id]
    );

    if (questionCheck.rows.length === 0) {
      return res.status(400).json({
        success: false,
        message: "Question not found",
      });
    }

    const result = await pool.query(
      `
      INSERT INTO learning_options
        (question_id, option_text, is_correct)
      VALUES
        ($1, $2, $3)
      RETURNING
        option_id,
        question_id,
        option_text,
        is_correct
      `,
      [
        question_id,
        option_text.trim(),
        Boolean(is_correct),
      ]
    );

    res.status(201).json({
      success: true,
      message: "Option created successfully!",
      option: result.rows[0],
    });
  } catch (error) {
    console.error("Create option error:", error);

    res.status(500).json({
      success: false,
      message: "Failed to create option",
      error: error.message,
    });
  }
});


// UPDATE OPTION
app.put("/api/options/:id", async (req, res) => {
  try {
    const { id } = req.params;

    const {
      question_id,
      option_text,
      is_correct,
    } = req.body;

    if (!question_id || !option_text || !option_text.trim()) {
      return res.status(400).json({
        success: false,
        message: "Question and option text are required",
      });
    }

    const questionCheck = await pool.query(
      `SELECT question_id FROM learning_questions WHERE question_id = $1`,
      [question_id]
    );

    if (questionCheck.rows.length === 0) {
      return res.status(400).json({
        success: false,
        message: "Question not found",
      });
    }

    const result = await pool.query(
      `
      UPDATE learning_options
      SET
        question_id = $1,
        option_text = $2,
        is_correct = $3
      WHERE option_id = $4
      RETURNING
        option_id,
        question_id,
        option_text,
        is_correct
      `,
      [
        question_id,
        option_text.trim(),
        Boolean(is_correct),
        id,
      ]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: "Option not found",
      });
    }

    res.json({
      success: true,
      message: "Option updated successfully!",
      option: result.rows[0],
    });
  } catch (error) {
    console.error("Update option error:", error);

    res.status(500).json({
      success: false,
      message: "Failed to update option",
      error: error.message,
    });
  }
});


// DELETE OPTION
app.delete("/api/options/:id", async (req, res) => {
  try {
    const { id } = req.params;

    const result = await pool.query(
      `
      DELETE FROM learning_options
      WHERE option_id = $1
      RETURNING option_id, option_text
      `,
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: "Option not found",
      });
    }

    res.json({
      success: true,
      message: "Option deleted successfully!",
      option: result.rows[0],
    });
  } catch (error) {
    console.error("Delete option error:", error);

    res.status(500).json({
      success: false,
      message: "Failed to delete option",
      error: error.message,
    });
  }
});


// ========================================`r`n// 404
// ========================================

app.use((req, res) => {
  res.status(404).json({
    success: false,
    message: "Route not found",
    path: req.originalUrl,
  });
});


// ========================================
// START SERVER
// ========================================

app.listen(PORT, () => {
  console.log(`Backend server running at http://localhost:${PORT}`);
});

