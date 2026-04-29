const express = require("express");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const { Pool } = require("pg");

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;
const SECRET = "secret";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

// 初回起動時にテーブル作成
async function init() {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS users (
      id SERIAL PRIMARY KEY,
      name TEXT,
      email TEXT UNIQUE,
      password TEXT
    );
  `);

  await pool.query(`
    CREATE TABLE IF NOT EXISTS posts (
      id SERIAL PRIMARY KEY,
      user_id INTEGER REFERENCES users(id),
      body TEXT,
      created_at TIMESTAMP DEFAULT NOW()
    );
  `);
}
init();

// 認証
function auth(req, res, next) {
  const token = req.headers.authorization?.split(" ")[1];
  if (!token) return res.status(401).json({ error: "no token" });

  try {
    req.user = jwt.verify(token, SECRET);
    next();
  } catch {
    res.status(401).json({ error: "invalid token" });
  }
}

// サインアップ
app.post("/signup", async (req, res) => {
  const { name, email, password } = req.body;
  const hash = bcrypt.hashSync(password, 10);

  try {
    await pool.query(
      "INSERT INTO users (name, email, password) VALUES ($1, $2, $3)",
      [name, email, hash]
    );
    res.json({ ok: true });
  } catch {
    res.status(400).json({ error: "email exists" });
  }
});

// ログイン
app.post("/login", async (req, res) => {
  const { email, password } = req.body;
  const result = await pool.query("SELECT * FROM users WHERE email = $1", [email]);
  const user = result.rows[0];

  if (!user || !bcrypt.compareSync(password, user.password)) {
    return res.status(401).json({ error: "invalid" });
  }

  const token = jwt.sign({ id: user.id, name: user.name }, SECRET);
  res.json({ token });
});

// 投稿
app.post("/posts", auth, async (req, res) => {
  const { body } = req.body;
  await pool.query(
    "INSERT INTO posts (user_id, body) VALUES ($1, $2)",
    [req.user.id, body]
  );
  res.json({ ok: true });
});

// タイムライン
app.get("/timeline", async (req, res) => {
  const result = await pool.query(`
    SELECT posts.id, posts.body, posts.created_at, users.name
    FROM posts
    JOIN users ON posts.user_id = users.id
    ORDER BY posts.created_at DESC
    LIMIT 50
  `);

  res.json(result.rows);
});

app.listen(PORT, () => console.log("Running on " + PORT));
