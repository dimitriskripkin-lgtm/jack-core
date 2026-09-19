#!/usr/bin/env python3
"""jack_gemini_cache.py — Context Caching für Gemini API.

Cached System-Prompt + Persona einmal, spart Token bei jedem Call.
Cache ist 1h gültig, wird automatisch erneuert.
"""
MODULE_VERSION = 1

import os, sys, json, time
J = os.path.expanduser("~/jack")
sys.path.insert(0, J)
from jack_log import get_logger
log = get_logger("jack_gemini_cache")

CACHE_STATE = os.path.join(J, "gemini_cache_state.json")
CACHE_TTL   = 3600  # 1 Stunde

def load_api_key():
    try:
        import jack_config as _jc
        return _jc.get("GEMINI_API_KEY", fallback=None)
    except Exception:
        return os.environ.get("GEMINI_API_KEY")

def load_persona():
    try:
        p = os.path.join(J, "jack_persona_kern.md")  # JACK_TUNE_BUGE
        return open(p).read()[:8000] if os.path.exists(p) else ""
    except Exception: return ""

def load_identity():
    try:
        p = os.path.join(J, "jack_identity.json")
        return json.dumps(json.load(open(p)))[:2000] if os.path.exists(p) else ""
    except Exception: return ""

def get_system_prompt():
    persona  = load_persona()
    identity = load_identity()
    return f"""Du bist JACK — Just Autonomous Command Kit.
Ein autonomes KI-System auf Android. Kein Cloud-Zwang. Offline-first.

PERSONA:
{persona[:4000]}

IDENTITÄT:
{identity[:1000]}

REGELN:
- Groq ist TALK-only, kein exec
- Keine Halluzinationen in den Graph schreiben
- Honor ist Wahrheit, GitHub kann stale sein
- Antworte auf Deutsch wenn Dima auf Deutsch schreibt
"""

def load_state():
    try: return json.load(open(CACHE_STATE))
    except Exception: return {}

def save_state(s):
    json.dump(s, open(CACHE_STATE, 'w'))

def get_cached_name() -> str | None:
    """Gibt gültigen Cache-Namen zurück oder None."""
    state = load_state()
    name = state.get("cache_name")
    ts   = state.get("created_at", 0)
    if name and (time.time() - ts) < CACHE_TTL:
        return name
    return None

def create_cache() -> str | None:
    """Erstellt neuen Gemini Context Cache. Gibt Cache-Name zurück."""
    api_key = load_api_key()
    if not api_key:
        log.warn("Kein API-Key — Cache nicht möglich")
        return None
    try:
        import urllib.request, urllib.error
        system_prompt = get_system_prompt()
        payload = json.dumps({
            "model": "models/gemini-2.0-flash-lite",
            "contents": [{
                "role": "user",
                "parts": [{"text": system_prompt}]
            }],
            "ttl": f"{CACHE_TTL}s"
        }).encode()
        url = f"https://generativelanguage.googleapis.com/v1beta/cachedContents?key={api_key}"
        req = urllib.request.Request(url, data=payload,
            headers={"Content-Type": "application/json"}, method="POST")
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        name = data.get("name")
        if name:
            save_state({"cache_name": name, "created_at": time.time()})
            log.info(f"Cache erstellt: {name}")
            return name
    except Exception as e:
        log.exception("Cache-Erstellung fehlgeschlagen", e)
    return None

def get_or_create() -> str | None:
    """Gibt Cache-Name zurück (aus State oder neu erstellt)."""
    name = get_cached_name()
    if name:
        log.info(f"Cache-Hit: {name[:40]}")
        return name
    return create_cache()

def invalidate():
    """Cache invalidieren (z.B. nach Persona-Update)."""
    save_state({})
    log.info("Cache invalidiert")

def run():
    """Waechter-Hook: Cache warmhalten."""
    name = get_or_create()
    return 1 if name else 0

if __name__ == "__main__":
    name = get_or_create()
    if name:
        print(f"Cache aktiv: {name[:60]}")
    else:
        print("Cache nicht verfügbar (API-Key fehlt oder Budget tot)")
