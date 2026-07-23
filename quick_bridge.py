from flask import Flask, jsonify
import subprocess
import os

app = Flask(__name__)

@app.route("/health")
def health():
    return jsonify({"status": "online", "user": os.environ.get("USER")})

@app.route("/cmd/<path:cmd>")
def execute(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return jsonify({"output": result.stdout, "error": result.stderr})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5005)
