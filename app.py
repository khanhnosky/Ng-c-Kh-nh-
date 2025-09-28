from flask import Flask, request, jsonify
import json, random, string, requests

app = Flask(__name__)

USERS_FILE = "users.json"
ACCS_FILE = "acc.txt"
USED_CODES = set()
API_TOKEN = "68cabdac49e05d64381ee4ea"

# ------------------ Helpers ------------------
def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def load_accs():
    try:
        with open(ACCS_FILE, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return []

# ------------------ Routes ------------------
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    users = load_users()
    if username in users:
        return jsonify({"error": "Tài khoản đã tồn tại!"}), 400

    users[username] = {"password": password, "spins": 0}
    save_users(users)
    return jsonify({"message": "Đăng ký thành công!"})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    users = load_users()
    if username not in users or users[username]["password"] != password:
        return jsonify({"error": "Sai tài khoản hoặc mật khẩu!"}), 401

    return jsonify({"message": "Đăng nhập thành công!"})

@app.route("/task", methods=["GET"])
def task():
    # Tạo link rút gọn bằng API linkm4
    long_url = "https://example.com/hoan-thanh-nhiem-vu"  # thay link nhiệm vụ thật vào đây
    api_url = f"https://link4m.co/api-shorten/v2?api={API_TOKEN}&url={long_url}"

    try:
        result = requests.get(api_url).json()
        if result["status"] != "thành công":
            return jsonify({"error": "Không tạo được link!"}), 500
        short_url = result["shortenedUrl"]
    except:
        return jsonify({"error": "API lỗi!"}), 500

    # Sinh 1 code xác nhận
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    USED_CODES.add(code)

    return jsonify({"task_link": short_url, "verify_code": code})

@app.route("/verify", methods=["POST"])
def verify():
    data = request.json
    username = data.get("username")
    code = data.get("code")

    users = load_users()
    if username not in users:
        return jsonify({"error": "User không tồn tại!"}), 400

    if code not in USED_CODES:
        return jsonify({"error": "Mã không hợp lệ hoặc đã dùng!"}), 400

    # cộng 1 lượt quay
    users[username]["spins"] += 1
    save_users(users)
    USED_CODES.remove(code)

    return jsonify({"message": "Xác nhận thành công! Bạn được +1 lượt quay."})

@app.route("/spin", methods=["POST"])
def spin():
    data = request.json
    username = data.get("username")

    users = load_users()
    if username not in users:
        return jsonify({"error": "User không tồn tại!"}), 400

    if users[username]["spins"] <= 0:
        return jsonify({"error": "Bạn không có lượt quay!"}), 400

    accs = load_accs()
    if not accs:
        return jsonify({"error": "Chưa có tài khoản nào trong hệ thống!"}), 400

    chosen = random.choice(accs)
    users[username]["spins"] -= 1
    save_users(users)

    return jsonify({"message": "Chúc mừng bạn quay trúng!", "account": chosen})

# ------------------ Main ------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)