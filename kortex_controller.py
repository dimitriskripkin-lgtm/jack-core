from kortex_memory import init_db, add_memory, search_memory, get_recent
#!/usr/bin/env python3
from flask import Flask, jsonify, request, Response, stream_with_context
from threading import Lock
from collections import deque
from datetime import datetime
from functools import wraps
import subprocess
import os
import json
import time
import secrets

app = Flask(__name__)

LOG_BUFFER = deque(maxlen=500)
LOCK = Lock()
JACK_PATH = os.path.expanduser("~/jack")
TOKEN_FILE = os.path.expanduser("~/.jack_secrets")


def get_kortex_token():
    token = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            for line in f:
                if "KORTEX_TOKEN=" in line:
                    token = line.strip().split("=", 1)[1].strip('"').strip("'")
    if not token:
        token = secrets.token_hex(24)
        with open(TOKEN_FILE, "a") as f:
            f.write("\nexport KORTEX_TOKEN=\"" + token + "\"\n")
        print("[KORTEX] Neuer Token generiert und in " + TOKEN_FILE + " gespeichert")
    return token


KORTEX_TOKEN = get_kortex_token()


def require_token(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("X-Kortex-Token", "")
        if auth != KORTEX_TOKEN:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return wrapper


def log_event(level, msg, source="system"):
    timestamp = datetime.now().isoformat()
    entry = {"timestamp": timestamp, "level": level, "source": source, "message": msg}
    with LOCK:
        LOG_BUFFER.append(entry)
    return entry


def exec_cmd(cmd, timeout=30):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, cwd=JACK_PATH)
        return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "Command timeout after " + str(timeout) + "s", "returncode": -1}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}


@app.route("/health")
def health():
    return jsonify({"status": "online", "timestamp": datetime.now().isoformat(), "user": os.environ.get("USER"), "jack_path": JACK_PATH})


@app.route("/logs/stream")
@require_token
def stream_logs():
    def generate():
        last_idx = 0
        while True:
            with LOCK:
                current = list(LOG_BUFFER)
            for entry in current[last_idx:]:
                yield "data: " + json.dumps(entry) + "\n\n"
            last_idx = len(current)
            time.sleep(0.5)
    return Response(stream_with_context(generate()), mimetype="text/event-stream")


@app.route("/logs")
@require_token
def get_logs():
    limit = request.args.get("limit", 50, type=int)
    with LOCK:
        logs = list(LOG_BUFFER)[-limit:]
    return jsonify({"logs": logs})


@app.route("/cmd", methods=["POST"])
@require_token
def execute_command():
    data = request.get_json()
    cmd = data.get("command", "").strip()
    if not cmd:
        return jsonify({"error": "No command provided"}), 400
    log_event("info", "Executing: " + cmd, "remote")
    result = exec_cmd(cmd)
    log_event("success" if result["success"] else "error", "Code " + str(result["returncode"]), "remote")
    return jsonify(result)


@app.route("/cmd/quick/<path:cmd>")
@require_token
def quick_cmd(cmd):
    log_event("info", "Quick: " + cmd, "remote")
    return jsonify(exec_cmd(cmd))


@app.route("/files")
@require_token
def list_files():
    try:
        files = os.listdir(JACK_PATH)
        file_info = []
        for f in files:
            path = os.path.join(JACK_PATH, f)
            stat = os.stat(path)
            file_info.append({"name": f, "size": stat.st_size, "is_dir": os.path.isdir(path)})
        return jsonify({"files": sorted(file_info, key=lambda x: x["name"])})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/sensors")
@require_token
def sensor_status():
    return jsonify({"status": "not_started"})


if __name__ == "__main__":
    log_event("info", "KORTEX Controller startet (mit Token-Auth)...", "system")
    print("[KORTEX] Token: " + KORTEX_TOKEN)
    print("[KORTEX] Header noetig: X-Kortex-Token: " + KORTEX_TOKEN)
    
@app.route('/memory/add', methods=['POST'])
def memory_add():
    data = request.get_json() or {}
    content = data.get('content', '')
    if not content:
        return jsonify({"error": "content required"}), 400
    return jsonify(add_memory(content, data.get('category','general'), data.get('source','api'), data.get('tags','')))

@app.route('/memory/search')
def memory_search():
    q = request.args.get('q', '')
    if not q:
        return jsonify({"error": "q required"}), 400
    return jsonify({"query": q, "results": search_memory(q, int(request.args.get('limit', 10)))})

@app.route('/memory/recent')
def memory_recent():
    return jsonify({"results": get_recent(int(request.args.get('limit', 20)))})

app.run(host="0.0.0.0", port=5005, debug=False)
