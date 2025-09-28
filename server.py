from flask import Flask, request, jsonify
import sqlite3, random, string, requests, os

app = Flask(__name__)
DB_FILE = "users.db"
ACCOUNTS_FILE = "accounts.txt"
USED_CODES = set()

API_TOKEN = "68cabdac49e05d64381ee4ea"  # key linkm4 của bạn
LONG_URL = "https://example.com/nhiem-vu"  # thay link nhiệm vụ thật vào đây

# ---------------- DB ----------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, spins INTEGER)''')
    conn.commit()
    conn.close()

def get_user(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT username, password, spins FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return row

def add_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO users VALUES (?, ?, ?)", (username, password, 10))
    conn.commit()
    conn.close()

def update_spins(username, spins):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET spins=? WHERE username=?", (spins, username))
    conn.commit()
    conn.close()

# ---------------- Routes ----------------
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username, password = data.get("username"), data.get("password")

    if get_user(username):
        return jsonify({"error": "User đã tồn tại!"}), 400

    add_user(username, password)
    return jsonify({"message": "Đăng ký thành công! Bạn có 10 lượt quay."})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username, password = data.get("username"), data.get("password")

    user = get_user(username)
    if not user or user[1] != password:
        return jsonify({"error": "Sai tài khoản hoặc mật khẩu!"}), 401

    return jsonify({"message": "Đăng nhập thành công!", "spins": user[2]})

@app.route("/get_task", methods=["GET"])
def get_task():
    # gọi API linkm4 để tạo short link
    api_url = f"https://link4m.co/api-shorten/v2?api={API_TOKEN}&url={LONG_URL}"
    try:
        result = requests.get(api_url).json()
        if result["status"] != "thành công":
            return jsonify({"error": "Không tạo được link"}), 500
        short_url = result["shortenedUrl"]
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # sinh code xác nhận
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    USED_CODES.add(code)
    return jsonify({"task_link": short_url, "verify_code": code})

@app.route("/submit_code", methods=["POST"])
def submit_code():
    data = request.json
    username, code = data.get("username"), data.get("code")

    user = get_user(username)
    if not user:
        return jsonify({"error": "User không tồn tại!"}), 400

    if code not in USED_CODES:
        return jsonify({"error": "Mã không hợp lệ hoặc đã dùng!"}), 400

    spins = user[2] + 1
    update_spins(username, spins)
    USED_CODES.remove(code)
    return jsonify({"message": "Xác nhận thành công! +1 lượt quay", "spins": spins})

@app.route("/spin", methods=["POST"])
def spin():
    data = request.json
    username = data.get("username")

    user = get_user(username)
    if not user:
        return jsonify({"error": "User không tồn tại!"}), 400

    if user[2] <= 0:
        return jsonify({"error": "Bạn không có lượt quay!"}), 400

    if not os.path.exists(ACCOUNTS_FILE):
        return jsonify({"error": "Không có accounts.txt!"}), 500

    with open(ACCOUNTS_FILE, "r") as f:
        accs = [line.strip() for line in f if line.strip()]

    if not accs:
        return jsonify({"error": "Hết acc rồi!"}), 400

    chosen = random.choice(accs)
    accs.remove(chosen)
    with open(ACCOUNTS_FILE, "w") as f:
        f.write("\n".join(accs))

    update_spins(username, user[2] - 1)
    return jsonify({"message": "Bạn quay trúng!", "account": chosen, "spins": user[2] - 1})

# ---------------- Main ----------------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
    @app.route("/")
def home():
    return "Tool Flask đang chạy thành công!"
