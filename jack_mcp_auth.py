#!/usr/bin/env python3
"""JACK_TUNE_MCPROLES - Token pro KI-Rolle, Rechte pro Rolle, Audit-Log.
Token-Datei: ~/jack/.jack_mcp_tokens, Zeilen ROLLE=token (chmod 600, NIE ins Repo/Chat).
Alter Einzel-Token (.jack_mcp_token) gilt als Rolle 'legacy' (alle Rechte) bis er entfernt wird.
CLI (nur im Termux auf dem Honor):
  python3 jack_mcp_auth.py rotate ROLLE   -> neuen Token erzeugen, speichern, NICHT anzeigen
  python3 jack_mcp_auth.py show ROLLE     -> Token anzeigen (nur auf dem Handy-Bildschirm)
  python3 jack_mcp_auth.py list           -> Rollen und Alter
  python3 jack_mcp_auth.py drop ROLLE     -> Rolle entfernen (z.B. legacy)
"""
import hmac, json, os, sys, time, secrets

J = os.environ.get("JACK_HOME", "/data/data/com.termux/files/home/jack")
TOKFILE = os.path.join(J, ".jack_mcp_tokens")
LEGACY = os.path.join(J, ".jack_mcp_token")
AUDIT = os.path.join(J, "logs", "mcp_audit.jsonl")
ROLES = ("claude", "nachtlauf", "gemini", "grok", "chatgpt")  # JACK_TUNE_CHATGPT

READ_ACTS_PREFIX = ("ro_",)
READ_ACTS = {"diag", "file_exists", "compile_ok", "sv_ok"}
NIGHT_DENY = {"sv_restart", "reload_module", "git_publish", "file_delete", "batch",
              "propose_fix", "approve_proposal", "exec_proposed", "write_proposed",
              "plan_try", "skill_confirm"}  # JACK_TUNE_NIGHTDENY2: keine Selbstfreigabe/Shell
CORE_FILES = ("jack_acts.py", "jack_mission_runner.py", "jack_mcp_server.py",
              "jack_handbuch_gate.py", "jack_kanal.py", "jack_arbeitsplatz.py", "jack_mcp_auth.py")
WER_OK = {"claude": {"claude"}, "nachtlauf": {"claude"}, "gemini": {"gemini"},
          "grok": {"grok"}, "chatgpt": {"chatgpt"}, "legacy": None}

SECRET_WORDS = ("token", "secret", "credential", "passw")  # JACK_TUNE_SECRETBLOCK
SECRET_NAMES = {"config.ini", ".netrc", ".env", ".git-credentials"}
FULL_ROLES = ("claude", "legacy")
# JACK_TUNE_CHATGPT: persoenliche Fakten (Graph/Gedaechtnis) bleiben fuer ChatGPT zu, bis Dima es freigibt
CHATGPT_DENY = {"graph_list_nodes", "graph_read_node", "graph_search", "graph_list_edges", "memory_search", "memory_recent"}

_cache = {"t": 0.0, "m": {}}
_fails = {}

def load_tokens():
    now = time.time()
    if now - _cache["t"] < 5:
        return _cache["m"]
    m = {}
    try:
        for line in open(TOKFILE, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                r, t = line.split("=", 1)
                if r.strip() and t.strip():
                    m[r.strip()] = t.strip().strip('"')
    except Exception:
        pass
    try:
        for line in open(LEGACY, encoding="utf-8"):
            if line.startswith("JACK_MCP_TOKEN="):
                t = line.strip().split("=", 1)[1].strip('"')
                if t:
                    m.setdefault("legacy", t)
    except Exception:
        pass
    _cache["t"], _cache["m"] = now, m
    return m

def role_for(auth_header):
    if not auth_header.startswith("Bearer "):
        return None
    got = auth_header[7:].strip().encode()
    hit = None
    for role, tok in load_tokens().items():  # alle pruefen, keine Abkuerzung
        if hmac.compare_digest(got, tok.encode()):
            hit = role
    if hit is None:  # JACK_TUNE_OAUTH: OAuth-Access-Token -> Rolle chatgpt
        try:
            import jack_mcp_oauth as _jo
            hit = _jo.role_of_token(got.decode())
        except Exception:
            hit = None
    return hit

def audit(role, tool, act, verdict, note=""):
    try:
        os.makedirs(os.path.dirname(AUDIT), exist_ok=True)
        with open(AUDIT, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "rolle": role,
                                "tool": tool, "act": act, "urteil": verdict, "note": note[:80]},
                               ensure_ascii=False) + "\n")
    except Exception:
        pass

def _path_check(role, name, args):
    """Geheimnis-Dateien fuer alle sperren, Nicht-Voll-Rollen nur JACK_HOME (gleiche Aufloesung wie der Server)."""
    if name not in ("read_file", "list_files"):
        return True, ""
    a = args if isinstance(args, dict) else {}
    p = str(a.get("path") or ("/storage/emulated/0/Download" if name == "list_files" else ""))
    full = os.path.realpath(p if p.startswith("/") else os.path.join(J, p))
    bn = os.path.basename(full).lower()
    if name == "read_file" and (bn in SECRET_NAMES or any(w in bn for w in SECRET_WORDS) or "/.ssh/" in full):
        return False, "Geheimnis-Datei gesperrt"
    if role == "chatgpt" and name == "read_file" and bn.endswith((".db", ".sqlite", ".sqlite3")):
        return False, "Datenbank-Datei fuer diese Rolle gesperrt"
    if role not in FULL_ROLES:
        jr = os.path.realpath(J)
        if not (full == jr or full.startswith(jr + os.sep)):
            return False, "Rolle darf nur JACK_HOME lesen"
    return True, ""

def check_call(role, name, args):
    """-> (ok, grund). Prueft ein tools/call. Keine Inhalte werden geloggt."""
    ok, why = _path_check(role, name, args)
    if not ok:
        return False, why
    if role in ("legacy", "claude") and name != "create_mission":
        return True, ""
    if role == "chatgpt" and name in CHATGPT_DENY:
        return False, "persoenliche Fakten fuer diese Rolle gesperrt"
    wer_ok = WER_OK.get(role)
    if isinstance(args, dict) and "wer" in args and wer_ok is not None:
        if str(args.get("wer", "")).lower() not in wer_ok:
            return False, "wer passt nicht zur Rolle"
    if name != "create_mission":
        return True, ""
    act = str((args or {}).get("act", ""))
    if role in ("legacy", "claude"):
        return True, ""
    if role in ("grok", "gemini", "chatgpt"):
        if act in READ_ACTS or act.startswith(READ_ACTS_PREFIX):
            return True, ""
        return False, "Rolle darf nur lesende Acts"
    if role == "nachtlauf":
        if act in NIGHT_DENY:
            return False, "Act in der Nacht verboten"
        ex = str((args or {}).get("extra", ""))
        if any(c in ex for c in CORE_FILES):
            return False, "Sicherheitskern gesperrt"
        if ".." in ex:
            return False, "Pfad mit .. gesperrt"
        return True, ""
    return False, "unbekannte Rolle"

class RoleMiddleware:
    """Reine ASGI-Middleware: Auth, Rollen-Check, Audit. Body wird gepuffert und wieder eingespielt."""
    def __init__(self, app):
        self.app = app

    async def _deny(self, send, code, msg):
        body = json.dumps({"error": msg}).encode()
        _h = [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]
        if code == 401:  # JACK_TUNE_OAUTH: Hinweis auf Resource-Metadaten (RFC 9728)
            try:
                import jack_mcp_oauth as _jo
                if not _jo.is_off():
                    _h.append((b"www-authenticate", ('Bearer resource_metadata="%s"' % _jo.resource_metadata_url()).encode()))
            except Exception:
                pass
        await send({"type": "http.response.start", "status": code, "headers": _h})
        await send({"type": "http.response.body", "body": body})

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        try:  # JACK_TUNE_OAUTH: nur die OAuth-Endpunkte sind ohne Bearer erreichbar
            import jack_mcp_oauth as _jo
            if _jo.is_public(scope.get("path", "")):
                return await self.app(scope, receive, send)
        except Exception:
            pass
        hdr = {k.decode().lower(): v.decode() for k, v in scope["headers"]}
        ip = hdr.get("cf-connecting-ip") or (scope.get("client") or ["?"])[0]
        if not load_tokens():
            audit("-", "-", "", "NEIN", "keine Tokens konfiguriert")
            return await self._deny(send, 503, "keine Tokens konfiguriert")
        role = role_for(hdr.get("authorization", ""))
        if not role:  # Sperre trifft nur ungueltige Tokens, gueltige kommen immer durch
            now = time.time()
            recent = [t for t in _fails.get(ip, []) if now - t < 60]
            if len(recent) >= 10:
                return await self._deny(send, 429, "zu viele Fehlversuche")
            recent.append(now); _fails[ip] = recent
            if len(_fails) > 500:
                _fails.clear()
            audit("?", "-", "", "NEIN", "ungueltiger Token")
            return await self._deny(send, 401, "unauthorized")
        if scope["method"] != "POST":
            return await self.app(scope, receive, send)
        chunks, more = [], True
        while more:
            msg = await receive()
            chunks.append(msg.get("body", b""))
            more = msg.get("more_body", False)
        body = b"".join(chunks)
        try:
            data = json.loads(body) if body else None
        except Exception:
            data = None
        for item in (data if isinstance(data, list) else [data]):
            if isinstance(item, dict) and item.get("method") == "tools/call":
                p = item.get("params") or {}
                name, args = p.get("name", ""), p.get("arguments") or {}
                ok, why = check_call(role, name, args)
                audit(role, name, str(args.get("act", "")) if isinstance(args, dict) else "",
                      "ja" if ok else "NEIN", why)
                if not ok:
                    return await self._deny(send, 403, "verboten: " + why)
        sent = {"d": False}
        async def replay():
            if not sent["d"]:
                sent["d"] = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()
        return await self.app(scope, replay, send)

def _write_all(m):
    lines = ["%s=%s" % (r, t) for r, t in m.items() if r != "legacy"]
    fd = os.open(TOKFILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))
    os.chmod(TOKFILE, 0o600)

def _cli(argv):
    cmd = argv[1] if len(argv) > 1 else "list"
    _cache["t"] = 0.0  # CLI liest immer frisch
    try:
        m = {r: t for r, t in load_tokens().items() if r != "legacy"}
    except Exception:
        m = {}
    if cmd == "list":
        for r in sorted(load_tokens()):
            print(r, "(Datei)" if r in m else "(alter Einzel-Token)")
    elif cmd == "rotate" and len(argv) > 2 and argv[2] in ROLES:
        m[argv[2]] = secrets.token_urlsafe(32)
        _write_all(m)
        print("Rolle %s: neuer Token gespeichert (wird nicht angezeigt)." % argv[2])
    elif cmd == "show" and len(argv) > 2:
        t = (m or {}).get(argv[2]) or load_tokens().get(argv[2])
        print(t if t else "Rolle unbekannt")
    elif cmd == "drop" and len(argv) > 2:
        if argv[2] == "legacy":
            print("legacy: Datei .jack_mcp_token von Hand entfernen: rm ~/jack/.jack_mcp_token")
        else:
            m.pop(argv[2], None); _write_all(m); print("Rolle entfernt:", argv[2])
    else:
        print(__doc__)

if __name__ == "__main__":
    _cli(sys.argv)
