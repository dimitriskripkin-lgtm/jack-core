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

try:  # JACK_TUNE_HBGATE
    import jack_handbuch_gate as _hg
    app = MCPServer("jack-server", instructions=_hg.INSTRUCTIONS)
except Exception:
    app = MCPServer("jack-server")

@app.tool()
def start_hier(wer: str = "") -> str:
    """RUFE DAS ZUERST AUF. Liefert den Pflichtzettel 00_START_HIER.md (Wahrheitsrangfolge, Pflichtablauf, eiserne Regeln, Schalter) plus Tagesquittung. Mit wer=claude|grok|gemini kommt dein Buero dazu. Pflicht vor jeder Aenderung."""
    import jack_handbuch_gate as _h
    t = _h.start_text()
    if wer:
        try:
            import json as _js, jack_arbeitsplatz as _ap  # JACK_TUNE_ARBEITSPLATZ
            t += "\n\n=== DEIN BUERO ===\n" + _js.dumps(_ap.buero(wer), ensure_ascii=False)[:6000]
            try:
                import jack_kanal as _k2
                t += "\n\nKANAL: %d ungelesene Nachrichten (ap_lese holt sie)." % _k2.ungelesen(wer)
                try:  # JACK_TUNE_AUFTRAEGE
                    _af = "/data/data/com.termux/files/home/jack/ARBEITSPLATZ/gemeinsam/auftraege.md"
                    import os as _os2
                    if _os2.path.exists(_af):
                        t += "\n\n=== AUFTRAEGE (gemeinsam/auftraege.md, Regeln: auftrag_regeln.md) ===\n" + open(_af, errors="ignore").read()[-2500:]
                except Exception:
                    pass
            except Exception:
                pass
        except Exception as _e:
            t += "\n\n(Buero nicht lesbar: %s)" % type(_e).__name__
    return t

@app.tool()
def buero(wer: str) -> str:
    """Dein Arbeitsplatz-Buero (claude|grok|gemini|dima): Regeln, offene Punkte, Eingang, Journal, Roadmap, Dateiliste."""
    import json as _js, jack_arbeitsplatz as _ap
    return _js.dumps(_ap.buero(wer), ensure_ascii=False)

@app.tool()
def ap_notiz(wer: str, pfad: str, text: str, modus: str = "anhaengen") -> str:
    """Schreibt in den Arbeitsplatz. pfad: BUEROS/<wer>/<datei> oder gemeinsam/<datei>. modus anhaengen|ersetzen. Fremdes Buero nur eingang.md anhaengen."""
    import json as _js, jack_arbeitsplatz as _ap
    return _js.dumps(_ap.schreiben(wer, pfad, text, modus), ensure_ascii=False)

@app.tool()
def ap_journal(wer: str, text: str) -> str:
    """Journal-Eintrag ins eigene Buero (Session-Ende-Pflicht)."""
    import json as _js, jack_arbeitsplatz as _ap
    return _js.dumps(_ap.journal(wer, text), ensure_ascii=False)

@app.tool()
def ap_post(wer: str, an: str, typ: str, text: str, re_id: int = 0) -> str:
    """Kanal-Post an eine andere KI (claude|grok|gemini|dima|alle). typ: frage|aufgabe|antwort|info|entscheidung|fertig. Rundengrenze 10 ohne Dima."""
    import jack_kanal as _k  # JACK_TUNE_KANAL
    return _k.post(wer, an, typ, text, re_id)

@app.tool()
def ap_lese(wer: str, seit_id: int = -1) -> str:
    """Neue Kanal-Post fuer dich holen (setzt deinen Lese-Cursor) plus aktuelle Reservierungen."""
    import jack_kanal as _k
    return _k.lese(wer, seit_id)

@app.tool()
def ap_claim(wer: str, ziel: str, aktion: str = "claim") -> str:
    """Modul/Aufgabe reservieren (60 Min): aktion claim|frei|verlaengern. Fremde Reservierung nicht anfassen."""
    import jack_kanal as _k
    return _k.claim(wer, ziel, aktion)

@app.tool()
def handbuch_index(suche: str = "") -> str:
    """Inhaltsverzeichnis des Betriebshandbuchs (Kapitel | Modul | Zweck). suche filtert nach Text."""
    import jack_handbuch_gate as _h
    return _h.index(suche)

@app.tool()
def handbuch_kapitel(name: str) -> str:
    """Liest das Betriebshandbuch-Kapitel eines Moduls, z.B. 'jack_mission_runner.py' oder '01_mission_runner.md'. Pflicht vor dem Patchen dieses Moduls."""
    import jack_handbuch_gate as _h
    return _h.kapitel(name)

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
def create_mission(act: str, description: str, extra: str = "{}", wait_seconds: int = 0) -> str:
    """PFLICHT: erst start_hier() aufrufen. Schreibende Acts verlangen extra.quittung (steht in der Ablehnung). Erstellt eine Mission in JACKs pending/-Ordner. act muss aus ALLOWED sein.
    extra: JSON-String mit zusaetzlichen Feldern z.B. {"file":"...", "old":"...", "new":"..."}.
    wait_seconds (JACK_TUNE_WAITRESULT): wenn >0, wartet bis zu diese Anzahl Sekunden
    (max 55) auf das Mission-Ergebnis und gibt es direkt im Feld 'result' zurueck,
    statt dass der Aufrufer separat pollen/read_file() muss.
    Erlaubte acts: sed_replace, py_replace, compile_ok, sv_ok, hb_ok, fact, grep_count, file_exists, diag."""
    import json as _j, os as _os
    from datetime import datetime as _dt
    import jack_acts as _acts  # JACK_TUNE_ACTS
    ALLOWED = set(_acts.names())
    if act not in ALLOWED:
        return _j.dumps({"error": f"act nicht erlaubt: {act}", "allowed": sorted(ALLOWED)})
    try:
        extra_d = _j.loads(extra) if extra.strip() else {}
    except Exception as e:
        return _j.dumps({"error": f"extra kein gueltiges JSON: {e}"})
    try:  # JACK_TUNE_HBGATE: Handbuch-Pflicht (fail-open)
        import jack_handbuch_gate as _hg2
        _gate = _hg2.gate(act, extra_d)
        if _gate:
            return _j.dumps(_gate, ensure_ascii=False)
    except Exception:
        pass
    PENDING = "/data/data/com.termux/files/home/jack/missions/pending"
    ts = _dt.now().strftime("%Y%m%d_%H%M%S")
    mid = f"m_{act}_{ts}"
    mission = {"id": mid, "act": act, "src": "claude_mcp",
               "ts": _dt.now().isoformat()[:19], "description": description}
    mission.update(extra_d)
    path = _os.path.join(PENDING, mid + ".json")
    with open(path, "w", encoding="utf-8") as fp:
        _j.dump(mission, fp, ensure_ascii=False, indent=2)
    result = {"ok": True, "mission_id": mid, "act": act, "path": path}
    if wait_seconds and wait_seconds > 0:
        import time as _tw
        LOGP = "/data/data/com.termux/files/home/jack/missions/logs/" + mid + ".json"
        _deadline = _tw.time() + min(int(wait_seconds), 55)
        _found = False
        while _tw.time() < _deadline:
            if _os.path.isfile(LOGP):
                try:
                    with open(LOGP, encoding="utf-8") as _lf:
                        result["result"] = _j.load(_lf)
                    _found = True
                except Exception as _e:
                    result["result_error"] = str(_e)
                    _found = True
                break
            _tw.sleep(1)
        if not _found:
            result["note"] = "noch nicht fertig nach " + str(wait_seconds) + "s"
    return _j.dumps(result)


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
        entries = [(f, _os.path.getmtime(_os.path.join(logs_dir, f))) for f in _os.listdir(logs_dir) if f.endswith(".json")]
        files = [f for f,_ in sorted(entries, key=lambda x: x[1], reverse=True)[:5]]
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
        names = sorted(_oslf.listdir(full))[:5000]  # JACK_TUNE_LISTCAP
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
        "PFLICHT_ZUERST": "start_hier() aufrufen und lesen. Vor Modul-Aenderung handbuch_kapitel(modul). Schreibende create_mission brauchen extra.quittung. Honor-Live-Datei ist Wahrheit.",
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
        "schreib_acts_erlaubt": sorted(n for n,a in __import__("jack_acts").ACTS.items() if a.get("freigabe")),
        "grenzen": [
            "Kein freies exec — nur jack_acts",
            "sv_restart ist ein Act",
            "SQLite-Datenbanken (Graph) nicht per Text-Ersetzung aenderbar — nur Dateien",
            "Secrets (config.ini, Tokens, .ssh) per read_file gesperrt",
        ],
        "rueckkanal": "Mission-Ergebnisse landen in jack_memory.db (intent=mission_result), lesbar ueber memory_recent",
        "version": "v31",
    }
    return json.dumps(info, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    import uvicorn, threading, time
    def _hb():
        while True:
            try:
                import jack_heartbeat
                jack_heartbeat.beat("jack_mcp")  # JACK_TUNE_MCPHB
            except Exception:
                pass
            time.sleep(30)
    threading.Thread(target=_hb, daemon=True).start()
    print("JACK MCP Server startet auf Port 8000 (mit Bearer-Token-Auth)...")
    print("Tools: graph_list_nodes, graph_read_node, graph_search, memory_search, memory_recent, create_mission")
    _asgi = app.streamable_http_app(host="0.0.0.0")
    _asgi.add_middleware(_JackAuthMiddleware)  # JACK_TUNE_MCPAUTH
    uvicorn.run(_asgi, host="127.0.0.1", port=8000, log_level="warning")
