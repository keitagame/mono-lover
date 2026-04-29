const express = require("express");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const db = require("./db");

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;
const SECRET = "secret"; // MVPなので固定値でOK

// 認証ミドルウェア
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
app.post("/signup", (req, res) => {
  const { name, email, password } = req.body;
  const hash = bcrypt.hashSync(password, 10);

  try {
    db.prepare("INSERT INTO users (name, email, password) VALUES (?, ?, ?)")
      .run(name, email, hash);
    res.json({ ok: true });
  } catch {
    res.status(400).json({ error: "email exists" });
  }
});

// ログイン
app.post("/login", (req, res) => {
  const { email, password } = req.body;
  const user = db.prepare("SELECT * FROM users WHERE email = ?").get(email);

  if (!user || !bcrypt.compareSync(password, user.password)) {
    return res.status(401).json({ error: "invalid" });
  }

  const token = jwt.sign({ id: user.id, name: user.name }, SECRET);
  res.json({ token });
});

// 投稿
app.post("/posts", auth, (req, res) => {
  const { body } = req.body;
  db.prepare("INSERT INTO posts (user_id, body) VALUES (?, ?)")
    .run(req.user.id, body);
  res.json({ ok: true });
});

// タイムライン（全ユーザーの投稿）
app.get("/timeline", (req, res) => {
  const posts = db.prepare(`
    SELECT posts.id, posts.body, posts.created_at, users.name
    FROM posts
    JOIN users ON posts.user_id = users.id
    ORDER BY posts.created_at DESC
    LIMIT 50
  `).all();

  res.json(posts);
});

app.listen(PORT, () => console.log("Running on " + PORT));
