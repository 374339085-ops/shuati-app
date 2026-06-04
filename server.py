# ============ 刷题软件 服务端 ============
# 在本机开 HTTP 服务，供学员连接
# 功能：老师注册/登录、班级管理、题库上传/下载、学员管理
import json, os, random, hashlib, threading, webbrowser
from flask import Flask, request, jsonify
from flask_cors import CORS

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "刷题数据")
SERVER_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server_data")
os.makedirs(SERVER_DATA_DIR, exist_ok=True)

app = Flask(__name__)
CORS(app)

# ============ 工具函数 ============
def load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default or {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def hash_pwd(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

# ============ 账号 ============
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

# ============ 班级数据 ============
CLASSES_FILE = os.path.join(SERVER_DATA_DIR, "classes.json")

def load_classes():
    return load_json(CLASSES_FILE, {})

def save_classes(classes):
    save_json(CLASSES_FILE, classes)

def gen_class_code():
    while True:
        code = str(random.randint(100000, 999999))
        classes = load_classes()
        if code not in classes:
            return code

def find_class_by_phone(phone, classes):
    """找到该老师创建的所有班级"""
    return [c for c in classes.values() if c.get("teacher") == phone]

def find_student_classes(student_phone, classes):
    """找到该学员加入的所有班级"""
    return [c for c in classes.values() if student_phone in c.get("students", [])]

def is_teacher(phone):
    """判断一个账号是否老师（最初注册的账号默认是老师）"""
    accounts = load_json(ACCOUNTS_FILE, {})
    return accounts.get(phone, {}).get("role", "teacher") == "teacher"

CHAT_FILE = os.path.join(SERVER_DATA_DIR, "chat.json")
def load_chat():
    return load_json(CHAT_FILE, {"messages": []})
def save_chat(chat):
    save_json(CHAT_FILE, chat)

app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# ============ API路由 ============

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()
    phone = data.get("phone", "").strip()
    pwd = data.get("password", "").strip()
    if not phone or not pwd:
        return jsonify({"success": False, "msg": "请输入手机号和密码"})
    accounts = load_json(ACCOUNTS_FILE, {})
    acc = accounts.get(phone)
    if not acc:
        return jsonify({"success": False, "msg": "账号不存在"})
    if acc["password"] != hash_pwd(pwd):
        return jsonify({"success": False, "msg": "密码错误"})
    return jsonify({"success": True, "role": acc.get("role", "teacher"), "phone": phone})

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json()
    phone = data.get("phone", "").strip()
    pwd = data.get("password", "").strip()
    role = data.get("role", "teacher")
    if not phone or not pwd:
        return jsonify({"success": False, "msg": "请填写完整信息"})
    if len(pwd) < 6:
        return jsonify({"success": False, "msg": "密码至少6位"})
    accounts = load_json(ACCOUNTS_FILE, {})
    if phone in accounts:
        return jsonify({"success": False, "msg": "该手机号已注册"})
    accounts[phone] = {"password": hash_pwd(pwd), "role": role}
    save_json(ACCOUNTS_FILE, accounts)
    # 初始化用户数据
    users = load_json(USERS_FILE, {})
    if phone not in users:
        users[phone] = {"wrongNotes": [], "settings": {"shuffle": False, "showExp": True, "autoNext": False}}
    save_json(USERS_FILE, users)
    return jsonify({"success": True})

@app.route("/api/create_class", methods=["POST"])
def api_create_class():
    data = request.get_json()
    teacher = data.get("teacher", "")
    class_name = data.get("name", "未命名班级")
    if not teacher:
        return jsonify({"success": False, "msg": "请先登录"})
    if not is_teacher(teacher):
        return jsonify({"success": False, "msg": "只有老师才能创建班级"})
    classes = load_classes()
    code = gen_class_code()
    classes[code] = {
        "code": code,
        "name": class_name,
        "teacher": teacher,
        "students": [],
        "banks": [],  # 老师上传的题库列表
        "created_at": time_str()
    }
    save_classes(classes)
    return jsonify({"success": True, "code": code, "name": class_name})

def time_str():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M")

@app.route("/api/get_teacher_classes", methods=["POST"])
def api_get_teacher_classes():
    data = request.get_json()
    teacher = data.get("teacher", "")
    classes_data = load_classes()
    mine = []
    for c in classes_data.values():
        if c.get("teacher") == teacher:
            banks_info = []
            for bname in c.get("banks", []):
                bank = load_json(os.path.join(DATA_DIR, f"{bname}.json"), [])
                banks_info.append({"name": bname, "count": len(bank)})
            mine.append({"code": c["code"], "name": c["name"],
                        "student_count": len(c.get("students", [])),
                        "banks": banks_info})
    return jsonify({"success": True, "classes": mine})

@app.route("/api/upload_bank", methods=["POST"])
def api_upload_bank():
    """老师上传题库到班级"""
    data = request.get_json()
    teacher = data.get("teacher", "")
    bank_name = data.get("bank_name", "")
    class_code = data.get("class_code", "")
    if not teacher or not bank_name or not class_code:
        return jsonify({"success": False, "msg": "参数不完整"})
    classes = load_classes()
    if class_code not in classes:
        return jsonify({"success": False, "msg": "班级不存在"})
    if classes[class_code]["teacher"] != teacher:
        return jsonify({"success": False, "msg": "你不是该班级的老师"})
    if bank_name not in classes[class_code].get("banks", []):
        classes[class_code].setdefault("banks", []).append(bank_name)
        save_classes(classes)
    return jsonify({"success": True})

@app.route("/api/remove_class_bank", methods=["POST"])
def api_remove_class_bank():
    """老师从班级移除题库"""
    data = request.get_json()
    teacher = data.get("teacher", "")
    bank_name = data.get("bank_name", "")
    class_code = data.get("class_code", "")
    classes = load_classes()
    if class_code in classes and classes[class_code]["teacher"] == teacher:
        classes[class_code]["banks"] = [b for b in classes[class_code].get("banks", []) if b != bank_name]
        save_classes(classes)
    return jsonify({"success": True})

@app.route("/api/join_class", methods=["POST"])
def api_join_class():
    data = request.get_json()
    student = data.get("student", "")
    code = data.get("code", "").strip()
    if not student or not code:
        return jsonify({"success": False, "msg": "参数不完整"})
    classes = load_classes()
    if code not in classes:
        return jsonify({"success": False, "msg": "班级码无效"})
    if student in classes[code].get("students", []):
        return jsonify({"success": True, "msg": "你已在该班级中"})
    classes[code].setdefault("students", []).append(student)
    save_classes(classes)
    return jsonify({"success": True, "class_name": classes[code]["name"]})

@app.route("/api/get_student_classes", methods=["POST"])
def api_get_student_classes():
    data = request.get_json()
    student = data.get("student", "")
    classes_data = load_classes()
    my_classes = []
    for c in classes_data.values():
        if student in c.get("students", []):
            banks_info = []
            for bname in c.get("banks", []):
                bank = load_json(os.path.join(DATA_DIR, f"{bname}.json"), [])
                banks_info.append({"name": bname, "count": len(bank)})
            my_classes.append({"code": c["code"], "name": c["name"],
                              "teacher": c["teacher"], "banks": banks_info})
    return jsonify({"success": True, "classes": my_classes})

@app.route("/api/get_bank_questions", methods=["POST"])
def api_get_bank_questions():
    data = request.get_json()
    bank_name = data.get("bank_name", "")
    bank = load_json(os.path.join(DATA_DIR, f"{bank_name}.json"), [])
    return jsonify({"success": True, "questions": bank})

@app.route("/api/save_bank_questions", methods=["POST"])
def api_save_bank_questions():
    """保存学员的做题进度到服务端，按用户区分"""
    data = request.get_json()
    phone = data.get("phone", "")
    bank_name = data.get("bank_name", "")
    questions = data.get("questions", [])
    if not phone or not bank_name:
        return jsonify({"success": False, "msg": "参数不完整"})
    # 每个用户的进度单独存
    progress_dir = os.path.join(SERVER_DATA_DIR, "progress", phone)
    os.makedirs(progress_dir, exist_ok=True)
    save_json(os.path.join(progress_dir, f"{bank_name}.json"), questions)
    return jsonify({"success": True})

@app.route("/api/load_bank_progress", methods=["POST"])
def api_load_bank_progress():
    """加载学员的做题进度"""
    data = request.get_json()
    phone = data.get("phone", "")
    bank_name = data.get("bank_name", "")
    progress_file = os.path.join(SERVER_DATA_DIR, "progress", phone, f"{bank_name}.json")
    questions = load_json(progress_file, None)
    return jsonify({"success": True, "questions": questions})

@app.route("/api/save_wrong_notes", methods=["POST"])
def api_save_wrong_notes():
    data = request.get_json()
    phone = data.get("phone", "")
    wrong_notes = data.get("wrong_notes", [])
    progress_dir = os.path.join(SERVER_DATA_DIR, "progress", phone)
    os.makedirs(progress_dir, exist_ok=True)
    save_json(os.path.join(progress_dir, "wrong_notes.json"), wrong_notes)
    return jsonify({"success": True})

@app.route("/api/load_wrong_notes", methods=["POST"])
def api_load_wrong_notes():
    data = request.get_json()
    phone = data.get("phone", "")
    progress_file = os.path.join(SERVER_DATA_DIR, "progress", phone, "wrong_notes.json")
    wrong_notes = load_json(progress_file, [])
    return jsonify({"success": True, "wrong_notes": wrong_notes})

@app.route("/api/get_class_students", methods=["POST"])
def api_get_class_students():
    data = request.get_json()
    teacher = data.get("teacher", "")
    class_code = data.get("class_code", "")
    classes = load_classes()
    if class_code not in classes or classes[class_code]["teacher"] != teacher:
        return jsonify({"success": False, "msg": "无权限"})
    students = []
    for s in classes[class_code].get("students", []):
        students.append(s)
    return jsonify({"success": True, "students": students})

# ============ Web版刷题页面 ============
WEB_HTML = open(os.path.join(os.path.dirname(__file__), 'server_templates', '刷题.html'), encoding='utf-8').read()

@app.route("/", methods=["GET"])
def web_index():
    return WEB_HTML

@app.route("/api/get_bank_questions_for_class", methods=["POST"])
def api_get_bank_questions_for_class():
    data = request.get_json()
    class_code = data.get("class_code", "")
    classes = load_classes()
    if class_code not in classes:
        return jsonify({"success": False, "msg": "班级不存在"})
    banks_info = []
    for bname in classes[class_code].get("banks", []):
        bank = load_json(os.path.join(DATA_DIR, f"{bname}.json"), [])
        banks_info.append({"name": bname, "count": len(bank)})
    return jsonify({"success": True, "banks": banks_info})

def get_local_ip():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

if __name__ == "__main__":
    local_ip = get_local_ip()
    print(f"\n{'='*50}")
    print(f"  刷题软件 - 服务端")
    print(f"  {'='*50}")
    print(f"  本机IP: {local_ip}")
    print(f"  端口: 5000")
    print(f"  学员连接地址: http://{local_ip}:5000")
    print(f"  {'='*50}")
    print(f"  请保持此窗口运行，关闭后学员将无法连接！")
    print(f"  {'='*50}\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
