"""JACK MCP Server (Phase 1, Qwen 22.08.2026)
Minimaler MCP-kompatibler HTTP-Server auf Xiaomi.
Nur 127.0.0.1 + Bearer-Token aus ~/.jack_secrets (MCP_TOKEN=...).
"""
import json, os, subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 8080
SECRETS = os.path.expanduser("~/.jack_secrets")

def get_token():
    try:
        with open(SECRETS) as f:
            for line in f:
                if line.startswith("MCP_TOKEN="):
                    return line.strip().split("=", 1)[1]
    except Exception:
        pass
    return None

class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _auth(self):
        tok = get_token()
        hdr = self.headers.get("Authorization", "")
        return bool(tok) and hdr == "Bearer " + tok

    def _send(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)
        self.wfile.flush()

    def do_GET(self):
        if self.path == "/ping":
            self._send({"status": "ok"})
        else:
            self._send({"error": "not found"}, 404)

    def do_POST(self):
        if not self._auth():
            self._send({"error": "unauthorized"}, 401)
            return
        ln = int(self.headers.get("Content-Length", 0))
        try:
            req = json.loads(self.rfile.read(ln) or b"{}")
        except Exception:
            req = {}
        m = req.get("method")
        rid = req.get("id")
        if m == "initialize":
            self._send({"jsonrpc": "2.0", "id": rid, "result": {"protocolVersion": "2024-11-05", "serverInfo": {"name": "jack-mcp", "version": "1.0"}}})
        elif m == "tools/list":
            self._send({"jsonrpc": "2.0", "id": rid, "result": {"tools": [{
                "name": "shell_exec",
                "description": "Fuehrt Shell-Befehl auf Xiaomi (JACK Worker) aus",
                "inputSchema": {"type": "object", "properties": {"cmd": {"type": "string"}}, "required": ["cmd"]}
            }]}})
        elif m == "tools/call":
            args = req.get("params", {}).get("arguments", {})
            cmd = args.get("cmd", "echo leer")
            if "rm -rf /" in cmd or "rm -rf ~" in cmd:
                self._send({"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": "BLOCKIERT: zerstoerender Befehl"}], "isError": True}})
                return
            try:
                r = subprocess.run(["sh", "-c", cmd], capture_output=True, text=True, timeout=30)
                out = (r.stdout + r.stderr)[:4000]
                self._send({"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": out}], "isError": r.returncode != 0}})
            except Exception as e:
                self._send({"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": str(e)[:500]}], "isError": True}})
        else:
            self._send({"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "method not found"}})

if __name__ == "__main__":
    srv = HTTPServer(("127.0.0.1", PORT), H)
    print(f"JACK MCP laeuft auf 127.0.0.1:{PORT}")
    srv.serve_forever()
