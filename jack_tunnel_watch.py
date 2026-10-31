#!/data/data/com.termux/files/usr/bin/python3
"""Tunnel-Waechter fuer JACK (15.10.2026)."""
import json, os, subprocess, time, urllib.error, urllib.request

H = os.path.expanduser("~/jack")
STATE = os.path.join(H, ".tunnel_watch_state.json")
OFF = os.path.join(H, ".tunnel_watch_off")
TUNNEL_URL = "https://mcp.jack-mcp-cloudflare.bid/mcp"
SECOND_URL = "https://example.com/"
INTERVAL_S = 120
COOLDOWN_S = 600
MAX_RESTARTS_H = 3
HTTP_TIMEOUT_S = 8
POST_RESTART_WAIT_S = 20

def _load():
    try:
        with open(STATE, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}

def _save(d):
    tmp = STATE + ".tmp"
    safe = {
        "ts": float(d.get("ts", time.time())),
        "status": str(d.get("status", "UNKNOWN"))[:40],
        "http": d.get("http"),
        "reason": str(d.get("reason", ""))[:160],
        "last_check": float(d.get("last_check", 0.0)),
        "last_restart": float(d.get("last_restart", 0.0)),
        "restarts": [float(x) for x in (d.get("restarts") or [])][-8:],
    }
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(safe, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STATE)
    return safe

def _http(url):
    req = urllib.request.Request(url, headers={"User-Agent": "JACK-TunnelWatch/1"}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S) as r:
            body = r.read(2048).decode("utf-8", "ignore")
            return int(r.status), body, ""
    except urllib.error.HTTPError as e:
        try:
            body = e.read(2048).decode("utf-8", "ignore")
        except Exception:
            body = ""
        return int(e.code), body, ""
    except Exception as e:
        return None, "", type(e).__name__

def _tunnel_probe(http_fn=None):
    http_fn = http_fn or _http
    code, body, err = http_fn(TUNNEL_URL)
    if code == 401:
        return "HEALTHY", code, "401"
    if code in (502, 530) or "1033" in (body or ""):
        return "DEAD", code, "cloudflare_%s" % ("1033" if "1033" in (body or "") else code)
    if code is None:
        return "DEAD", None, "timeout_or_network:" + (err or "unknown")
    return "UNKNOWN", code, "unexpected_http_%s" % code

def _network_ok(http_fn=None):
    http_fn = http_fn or _http
    code, _body, _err = http_fn(SECOND_URL)
    return code is not None

def _origin_ok(http_fn=None):
    """JACK_TUNE_ORIGINCHECK (17.10.2026): antwortet der MCP-Server lokal? Dann ist er nicht das Problem.
    Am 17.10. 11:45 wurde cloudflared neu gestartet, nur weil jack_mcp gerade neu startete (502)."""
    http_fn = http_fn or _http
    code, _body, _err = http_fn("http://127.0.0.1:8000/mcp")
    return code is not None

def _restart_cloudflared():
    try:
        # JACK_TUNE_TUNNELGRACE + JACK_TUNE_SVNEUSTART (31.10.2026, Kap 285/312): wartet die cloudflared-
        # Grace-Period ab, beendet einen haengenden alten Prozess hart, Erfolg nur mit neuer PID.
        import jack_svneustart as _svn
        r = _svn.neustart("cloudflared", warte_s=45)
        return bool(r.get("ok")), (0 if r.get("ok") else 1)
    except Exception:
        return False, -1

def _notify_text(prev, cur):
    status = cur.get("status")
    if status == prev:
        return ""
    if status == "NETWORK_DOWN":
        return "Tunnel-Waechter: Netz selbst nicht erreichbar; cloudflared NICHT neu gestartet."
    if status == "RESTART_LIMIT":
        return "Tunnel-Waechter: Tunnel tot, Neustartlimit %d/Stunde erreicht." % MAX_RESTARTS_H
    if status == "COOLDOWN":
        return "Tunnel-Waechter: Tunnel tot, Neustart-Cooldown aktiv."
    if status == "RECOVERED":
        return "Tunnel-Waechter: cloudflared neu gestartet; Tunnel danach wieder mit HTTP 401 belegt."
    if status == "UNKNOWN":
        return "Tunnel-Waechter: Zustand UNKNOWN; kein Reparaturerfolg ohne HTTP-401-Nachweis."
    if status == "HEALTHY" and prev not in ("", "HEALTHY"):
        return "Tunnel-Waechter: Tunnel wieder gesund (HTTP 401)."
    return ""

def check(force=False, now=None, http_fn=None, restart_fn=None, sleep_fn=None):
    now = float(time.time() if now is None else now)
    restart_fn = restart_fn or _restart_cloudflared
    sleep_fn = sleep_fn or time.sleep
    old = _load()
    prev = str(old.get("status", ""))
    if os.path.exists(OFF):
        d = dict(old)
        d.update(ts=now, status="DISABLED", reason="switch", last_check=now)
        d = _save(d)
        return {"ran": True, "status": "DISABLED", "notify": _notify_text(prev, d)}
    last_check = float(old.get("last_check", 0.0) or 0.0)
    if not force and now - last_check < INTERVAL_S:
        return {"ran": False, "status": prev or "UNKNOWN", "notify": ""}
    restarts = [float(x) for x in (old.get("restarts") or []) if now - float(x) < 3600]
    base = {"ts": now, "last_check": now, "last_restart": float(old.get("last_restart", 0.0) or 0.0), "restarts": restarts}
    state, code, reason = _tunnel_probe(http_fn)
    if state == "HEALTHY":
        d = _save(dict(base, status="HEALTHY", http=code, reason=reason))
        return {"ran": True, "status": d["status"], "notify": _notify_text(prev, d)}
    if state == "UNKNOWN":
        d = _save(dict(base, status="UNKNOWN", http=code, reason=reason))
        return {"ran": True, "status": d["status"], "notify": _notify_text(prev, d)}
    if not _network_ok(http_fn):
        d = _save(dict(base, status="NETWORK_DOWN", http=code, reason=reason))
        return {"ran": True, "status": d["status"], "notify": _notify_text(prev, d)}
    if not _origin_ok(http_fn):  # JACK_TUNE_ORIGINCHECK: MCP selbst ist weg, cloudflared neu starten hilft nicht
        d = _save(dict(base, status="ORIGIN_DOWN", http=code, reason=reason))
        return {"ran": True, "status": d["status"], "notify": _notify_text(prev, d)}
    if len(restarts) >= MAX_RESTARTS_H:
        d = _save(dict(base, status="RESTART_LIMIT", http=code, reason=reason))
        return {"ran": True, "status": d["status"], "notify": _notify_text(prev, d)}
    last_restart = float(base["last_restart"])
    if last_restart and now - last_restart < COOLDOWN_S:
        d = _save(dict(base, status="COOLDOWN", http=code, reason=reason))
        return {"ran": True, "status": d["status"], "notify": _notify_text(prev, d)}
    ok_restart, rc = restart_fn()
    restarts.append(now)
    base["restarts"] = restarts
    base["last_restart"] = now
    if not ok_restart:
        d = _save(dict(base, status="UNKNOWN", http=code, reason="sv_restart_rc_%s" % rc))
        return {"ran": True, "status": d["status"], "notify": _notify_text(prev, d)}
    sleep_fn(POST_RESTART_WAIT_S)
    after, after_code, after_reason = _tunnel_probe(http_fn)
    if after == "HEALTHY":
        d = _save(dict(base, ts=time.time(), status="RECOVERED", http=after_code, reason="post_restart_401"))
    else:
        d = _save(dict(base, ts=time.time(), status="UNKNOWN", http=after_code, reason="post_restart_" + after_reason))
    return {"ran": True, "status": d["status"], "notify": _notify_text(prev, d)}

def status():
    return _load()

if __name__ == "__main__":
    print(json.dumps(check(force=True), ensure_ascii=False))
