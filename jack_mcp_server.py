#!/usr/bin/env python3
"""JACK MCP Server — Tools für externe KIs (Claude, Gemini, Qwen)"""
from mcp.server.mcpserver import MCPServer
import sqlite3
import json
import os

JACK_HOME = "/data/data/com.termux/files/home/jack"
GRAPH_DB = os.path.join(JACK_HOME, "jack_graph.db")
MEMORY_DB = os.path.join(JACK_HOME, "jack_memory.db")

app = MCPServer("jack-server")

@app.tool()
def graph_list_nodes(limit: int = 20) -> str:
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
               "sed_replace","py_replace"}
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

if __name__ == "__main__":
    print("JACK MCP Server startet auf Port 8000...")
    print("Tools: graph_list_nodes, graph_read_node, graph_search, memory_search, memory_recent")
    app.run(transport="streamable-http", host="0.0.0.0", port=8000)  # JACK_TUNE_MCPTAILSCALE
