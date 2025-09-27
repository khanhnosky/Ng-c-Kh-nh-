from flask import Flask, request, jsonify
import sqlite3, random, os

app = Flask(__name__)

DB_NAME = "users.db"
ACCOUNTS_FILE = "accounts.txt"

# ---- DB setup ----
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT,
                        spins INTEGER DEFAULT 0
                    )""")
        c.execute("""CREATE TABLE IF NOT EXISTS codes_used (
                        code TEXT PRIMARY KEY
                    )""")
    print("DB ready.")

init_db()

# ---- Helper ----
def user_exists(username, password):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        return c.fetchone()

# ---- Routes ----
@app.route("/")
def home():
    return "Flask Server Railway OK!"

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username, password = data.get("username"), data.get("password")
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password, spins) VALUES (?, ?, ?)", (username, password, 10))
            conn.commit()
            return jsonify({"status": "success", "message": "Register OK, +10 spins"})
        except sqlite3.IntegrityError:
            return jsonify({"status": "fail", "message": "User exists"})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username, password = data.get("username"), data.get("password")
    if user_exists(username, password):
        return jsonify({"status": "success", "message": "Login OK"})
    return jsonify({"status": "fail", "message": "Wrong username or password"})

@app.route("/get_task", methods=["GET"])
def get_task():
    # fake nhiệm vụ → trả về 1 code random
    code = str(random.randint(100000, 999999))
    return jsonify({"task": f"Truy cập linkm4 để lấy mã: {code}", "code": code})

@app.route("/submit_code", methods=["POST"])
def submit_code():
    data = request.json
    username, password, code = data.get("username"), data.get("password"), data.get("code")

    if not user_exists(username, password):
        return jsonify({"status": "fail", "message": "Login required"})

    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM codes_used WHERE code=?", (code,))
        if c.fetchone():
            return jsonify({"status": "fail", "message": "Code already used"})

        c.execute("INSERT INTO codes_used (code) VALUES (?)", (code,))
        c.execute("UPDATE users SET spins = spins + 1 WHERE username=?", (username,))
        conn.commit()
    return jsonify({"status": "success", "message": "+1 spin"})

@app.route("/spin", methods=["POST"])
def spin():
    data = request.json
    username, password = data.get("username"), data.get("password")

    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT spins FROM users WHERE username=? AND password=?", (username, password))
        row = c.fetchone()
        if not row:
            return jsonify({"status": "fail", "message": "Login required"})

        spins = row[0]
        if spins <= 0:
            return jsonify({"status": "fail", "message": "No spins left"})

        # trừ 1 spin
        c.execute("UPDATE users SET spins = spins - 1 WHERE username=?", (username,))
        conn.commit()

    # random acc từ file
    if not os.path.exists(ACCOUNTS_FILE):
        return jsonify({"status": "fail", "message": "No accounts file"})

    with open(ACCOUNTS_FILE, "r") as f:
        lines = f.readlines()

    if not lines:
        return jsonify({"status": "fail", "message": "No accounts left"})

    acc = random.choice(lines).strip()
    lines.remove(acc + "\n")  # xóa để không bị trùng

    with open(ACCOUNTS_FILE, "w") as f:
        f.writelines(lines)

    return jsonify({"status": "success", "account": acc})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)