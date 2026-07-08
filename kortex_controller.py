#!/usr/bin/env python3
from flask import Flask, jsonify, request, Response, stream_with_context
from threading import Lock
from collections import deque
from datetime import datetime
import subprocess
import os
import json
import time

app = Flask(__name__)

LOG_BUFFER = deque(maxlen=500)
LOCK = Lock()
JACK_PATH = os.path.expanduser("~/jack")

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
        return {"success": False, "stdout": "", "stderr": f"Command timeout after {timeout}s", "returncode": -1}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}

@app.route("/health")
def health():
    return jsonify({"status": "online", "timestamp": datetime.now().isoformat(), "user": os.environ.get("USER"), "jack_path": JACK_PATH})

@app.route("/logs/stream")
def stream_logs():
    def generate():
        last_idx = 0
        while True:
            with LOCK:
                current = list(LOG_BUFFER)
            for entry in current[last_idx:]:
                yield f"data: {json.dumps(entry)}\n\n"
            last_idx = len(current)
            time.sleep(0.5)
    return Response(stream_with_context(generate()), mimetype="text/event-stream")

@app.route("/logs")
def get_logs():
    limit = request.args.get("limit", 50, type=int)
    with LOCK:
        logs = list(LOG_BUFFER)[-limit:]
    return jsonify({"logs": logs})

@app.route("/cmd", methods=["POST"])
def execute_command():
    data = request.get_json()
    cmd = data.get("command", "").strip()
    if not cmd:
        return jsonify({"error": "No command provided"}), 400
    log_event("info", f"Executing: {cmd}", "claude")
    result = exec_cmd(cmd)
    log_event("success" if result["success"] else "error", f"Code {result['returncode']}", "claude")
    return jsonify(result)

@app.route("/cmd/quick/<path:cmd>")
def quick_cmd(cmd):
    log_event("info", f"Quick: {cmd}", "claude")
    return jsonify(exec_cmd(cmd))

@app.route("/files")
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
def sensor_status():
    return jsonify({"status": "not_started"})

if __name__ == "__main__":
    log_event("info", "KORTEX Controller starting...", "system")
    app.run(host="0.0.0.0", port=5005, debug=False)
