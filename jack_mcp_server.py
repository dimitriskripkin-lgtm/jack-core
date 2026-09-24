#!/usr/bin/env python3
"""JACK MCP Server — Tools für externe KIs (Claude, Gemini, Qwen)"""
from mcp.server.mcpserver import MCPServer

_JACK_MCP_TOKEN = None
try:
    with open("/data/data/com.termux/files/home/jack/.jack_mcp_token") as _tf:
        for _line in _tf:
            if _line.startswith("JACK_MCP_TOKEN="):
                _JACK_MCP_TOKEN = _line.strip().split("=",1)[1].strip('"')
except Exception:
    pass

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class _JackAuthMiddleware(BaseHTTPMiddleware):  # JACK_TUNE_MCPAUTH
    async def dispatch(self, request, call_next):
        if _JACK_MCP_TOKEN:
            auth = request.headers.get("authorization", "")
            if auth != f"Bearer {_JACK_MCP_TOKEN}":
                return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)
import sqlite3
import json
import os

JACK_HOME = "/data/data/com.termux/files/home/jack"
GRAPH_DB = os.path.join(JACK_HOME, "jack_graph.db")
MEMORY_DB = os.path.join(JACK_HOME, "jack_memory.db")

app = MCPServer("jack-server")

@app.tool()
def graph_list_nodes(limit: int = 200) -> str:
    """Listet Knoten im JACK-Graph auf (typ, name, wert)."""
    try:
        conn = sqlite3.connect(GRAPH_DB)
        cur = conn.execute("SELECT typ, name, wert, src FROM nodes ORDER BY ts DESC LIMIT ?", (limit,))
        nodes = [{"typ": r[0], "name": r[1], "wert": r[2], "src": r[3]} for r in cur.fetchall()]
        conn.close()
        return json.dumps(nodes, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

@app.tool()
def graph_read_node(node_id: str) -> str:
    """Liest einen Knoten per ID (z.B. 'person:dima', 'fakt:katze')."""
    try:
        conn = sqlite3.connect(GRAPH_DB)
        cur = conn.execute("SELECT typ, name, wert, src, ts FROM nodes WHERE id=?", (node_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            return json.dumps({"id": node_id, "typ": row[0], "name": row[1], "wert": row[2], "src": row[3], "ts": row[4]}, ensure_ascii=False)
        else:
            return json.dumps({"error": f"Knoten {node_id} nicht gefunden"})
    except Exception as e:
        return json.dumps({"error": str(e)})

@app.tool()
def graph_search(query: str) -> str:
    """Sucht Knoten nach Name oder Wert."""
    try:
        conn = sqlite3.connect(GRAPH_DB)
        cur = conn.execute("SELECT id, typ, name, wert FROM nodes WHERE name LIKE ? OR wert LIKE ? LIMIT 10", (f"%{query}%", f"%{query}%"))
        results = [{"id": r[0], "typ": r[1], "name": r[2], "wert": r[3]} for r in cur.fetchall()]
        conn.close()
        return json.dumps(results, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

@app.tool()
def memory_search(query: str, limit: int = 10) -> str:
    """Durchsucht das Gedächtnis (memory-Tabelle) nach cmd oder result."""
    try:
        conn = sqlite3.connect(MEMORY_DB)
        cur = conn.execute("SELECT id, cmd, result, intent, timestamp FROM memory WHERE cmd LIKE ? OR result LIKE ? ORDER BY timestamp DESC LIMIT ?", (f"%{query}%", f"%{query}%", limit))
        results = [{"id": r[0], "cmd": r[1][:150], "result": r[2][:200], "intent": r[3], "timestamp": r[4]} for r in cur.fetchall()]
        conn.close()
        return json.dumps(results, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

@app.tool()
def memory_recent(limit: int = 5) -> str:
    """Zeigt die letzten Gedächtnis-Einträge."""
    try:
        conn = sqlite3.connect(MEMORY_DB)
        cur = conn.execute("SELECT id, cmd, result, intent, timestamp FROM memory ORDER BY timestamp DESC LIMIT ?", (limit,))
        results = [{"id": r[0], "cmd": r[1][:150], "result": r[2][:200], "intent": r[3], "timestamp": r[4]} for r in cur.fetchall()]
        conn.close()
        return json.dumps(results, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@app.tool()
def create_mission(act: str, description: str, extra: str = "{}") -> str:
    """Erstellt eine Mission in JACKs pending/-Ordner. act muss aus ALLOWED sein.
    extra: JSON-String mit zusaetzlichen Feldern z.B. {"file":"...", "old":"...", "new":"..."}.
    Erlaubte acts: sed_replace, py_replace, compile_ok, sv_ok, hb_ok, fact, grep_count, file_exists, diag."""
    import json as _j, os as _os
    from datetime import datetime as _dt
    ALLOWED = {"shadow_report","talk_contract","fact","diag","no_chrome_src","ui_none",
               "classify_is","compile_ok","explain_ok","sv_ok","mtime_fresh","json_valid",
               "no_secret","grep_count","line_check","hb_ok","file_exists","line_count",
               "sed_replace","py_replace","file_create","file_delete","batch"}
    if act not in ALLOWED:
        return _j.dumps({"error": f"act nicht erlaubt: {act}", "allowed": sorted(ALLOWED)})
    try:
        extra_d = _j.loads(extra) if extra.strip() else {}
    except Exception as e:
        return _j.dumps({"error": f"extra kein gueltiges JSON: {e}"})
    PENDING = "/data/data/com.termux/files/home/jack/missions/pending"
    ts = _dt.now().strftime("%Y%m%d_%H%M%S")
    mid = f"m_{act}_{ts}"
    mission = {"id": mid, "act": act, "src": "claude_mcp",
               "ts": _dt.now().isoformat()[:19], "description": description}
    mission.update(extra_d)
    path = _os.path.join(PENDING, mid + ".json")
    with open(path, "w", encoding="utf-8") as fp:
        _j.dump(mission, fp, ensure_ascii=False, indent=2)
    return _j.dumps({"ok": True, "mission_id": mid, "act": act, "path": path})


@app.tool()
def mission_status() -> str:
    """Uebersicht ueber die Mission-Warteschlange: Anzahl pending/done/fail und die letzten 5 Ergebnisse."""
    import json as _j, os as _os
    base = "/data/data/com.termux/files/home/jack/missions"
    def _count(d):
        p = _os.path.join(base, d)
        return len([f for f in _os.listdir(p) if f.endswith(".json")]) if _os.path.isdir(p) else 0
    counts = {"pending": _count("pending"), "done": _count("done"), "fail": _count("fail")}
    logs_dir = _os.path.join(base, "logs")
    recent = []
    if _os.path.isdir(logs_dir):
        files = sorted(_os.listdir(logs_dir), reverse=True)[:5]
        for fn in files:
            try:
                with open(_os.path.join(logs_dir, fn), encoding="utf-8") as fp:
                    rec = _j.load(fp)
                recent.append({"id": rec.get("id"), "ok": rec.get("ok"), "note": str(rec.get("note",""))[:100]})
            except Exception:
                pass
    return _j.dumps({"counts": counts, "recent": recent})


@app.tool()
def read_file(path: str, lines: int = 100, plain: bool = False) -> str:
    """Liest Datei in JACK_HOME. plain=True: nur Text, kein JSON-Mantel."""
    import os as _osrf
    try:
        full = _osrf.path.realpath(path if path.startswith("/") else _osrf.path.join(JACK_HOME, path))
        roots = [
            _osrf.path.realpath(JACK_HOME),
            _osrf.path.realpath("/storage/emulated/0"),
        ]
        ok_root = any(full == r or full.startswith(r + _osrf.sep) for r in roots)
        if not ok_root:
            return json.dumps({"error": "Pfad nicht in JACK_HOME oder internem Speicher"})
        blocked = {"config.ini", ".jack_mcp_token"}
        if _osrf.path.basename(full) in blocked or "/.ssh/" in full:
            return json.dumps({"error": "Datei gesperrt (Secrets)"})
        if not _osrf.path.isfile(full):
            return json.dumps({"error": f"Datei nicht gefunden: {full}"})
        with open(full, "r", encoding="utf-8", errors="replace") as fp:
            content = "".join(fp.readlines()[:max(1,min(lines,5000))])  # JACK_TUNE_READCAP
        if plain:
            return content
        return json.dumps({"path": full, "content": content}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


@app.tool()
def list_files(path: str = "/storage/emulated/0/Download") -> str:
    """Listet Dateien in JACK_HOME oder Download. Nur Namen, kein Inhalt."""
    import os as _oslf
    try:
        full = _oslf.path.realpath(path if path.startswith("/") else _oslf.path.join(JACK_HOME, path))
        roots = [
            _oslf.path.realpath(JACK_HOME),
            _oslf.path.realpath("/storage/emulated/0"),
        ]
        if not any(full == r or full.startswith(r + _oslf.sep) for r in roots):
            return json.dumps({"error": "Pfad nicht erlaubt"})
        if not _oslf.path.isdir(full):
            return json.dumps({"error": "kein Ordner"})
        names = sorted(_oslf.listdir(full))[:400]
        return json.dumps({"path": full, "n": len(names), "names": names}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


@app.tool()
def graph_list_edges(limit: int = 30) -> str:
    """Listet Kanten (Beziehungen) im JACK-Graph auf: a -rel-> b."""
    try:
        conn = sqlite3.connect(GRAPH_DB)
        cur = conn.execute("SELECT a, rel, b, src FROM edges ORDER BY ts DESC LIMIT ?", (limit,))
        edges = [{"a": r[0], "rel": r[1], "b": r[2], "src": r[3]} for r in cur.fetchall()]
        conn.close()
        return json.dumps(edges, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@app.tool()
def describe_system() -> str:
    """Selbstbeschreibung fuer neue KIs: Tools, Grenzen, aktuelle Freigaben. Kein Onboarding-Dokument noetig."""
    info = {
        "system": "JACK",
        "beschreibung": "Autonomes Reparatur- und Programmiersystem auf zwei Android-Phones (Honor=Gehirn, Xiaomi=Muskel)",
        "tools": [
            {"name": "graph_list_nodes", "zugriff": "lesend", "beschreibung": "Fakten-Knoten im Graph"},
            {"name": "graph_read_node", "zugriff": "lesend", "beschreibung": "Ein Knoten per ID"},
            {"name": "graph_search", "zugriff": "lesend", "beschreibung": "Knoten nach Name/Wert suchen"},
            {"name": "graph_list_edges", "zugriff": "lesend", "beschreibung": "Beziehungen zwischen Knoten"},
            {"name": "memory_search", "zugriff": "lesend", "beschreibung": "Gespraechsverlauf durchsuchen"},
            {"name": "memory_recent", "zugriff": "lesend", "beschreibung": "Letzte Eintraege, inkl. Mission-Ergebnisse"},
            {"name": "read_file", "zugriff": "lesend", "beschreibung": "Datei in JACK_HOME lesen, Secrets gesperrt"},
            {"name": "create_mission", "zugriff": "schreibend", "beschreibung": "Mission queuen, wird automatisch ausgefuehrt"},
        ],
        "schreib_acts_erlaubt": ["sed_replace", "py_replace", "compile_ok", "sv_ok", "hb_ok",
                                  "fact", "grep_count", "file_exists", "diag"],
        "grenzen": [
            "Kein freies exec — nur die ALLOWED-Liste an Acts",
            "Dienst-Neustarts nach Code-Aenderungen kann keine KI selbst ausloesen (kein Mission-Act dafuer)",
            "SQLite-Datenbanken (Graph) nicht per Text-Ersetzung aenderbar — nur Dateien",
            "Secrets (config.ini, Tokens, .ssh) per read_file gesperrt",
        ],
        "rueckkanal": "Mission-Ergebnisse landen in jack_memory.db (intent=mission_result), lesbar ueber memory_recent",
        "version": "v31",
    }
    return json.dumps(info, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    import uvicorn
    print("JACK MCP Server startet auf Port 8000 (mit Bearer-Token-Auth)...")
    print("Tools: graph_list_nodes, graph_read_node, graph_search, memory_search, memory_recent, create_mission")
    _asgi = app.streamable_http_app(host="0.0.0.0")
    _asgi.add_middleware(_JackAuthMiddleware)  # JACK_TUNE_MCPAUTH
    uvicorn.run(_asgi, host="0.0.0.0", port=8000, log_level="warning")
