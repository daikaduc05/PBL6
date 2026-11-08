require("dotenv").config({ path: __dirname + "/.env" });

const { Pool } = require("pg");

const pool = new Pool({
  host: process.env.DB_HOST || "localhost",
  port: Number(process.env.DB_PORT || 5432),
  user: process.env.DB_USER || "postgres",
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME || "pbl6",
});

pool.on("connect", () => {
  console.log("PostgreSQL connected successfully!");
});

pool.on("error", (err) => {
  console.error("PostgreSQL connection error:", err.message);
});

module.exports = pool;