import subprocess, os, re

BLOCK = ['rm -rf /', 'mkfs', 'dd if=', ':(){', 'chmod -R 777 /',
         'id_jack', '.ssh/', 'api_key', 'API_KEY',
         'shutdown', 'reboot', '> /dev/sd']

def pruefe(cmd):
    low = cmd.lower()
    for b in BLOCK:
        if b.lower() in low:
            return False, 'BLOCKIERT: ' + b
    if len(cmd) > 4000:
        return False, 'BLOCKIERT: zu lang'
    return True, 'OK'


def tap_text(query, partial=True):
    """Text-Tap via jack_vision_selector (Roadmap: vor Monkey/Koordinaten)."""
    q = (query or "").strip()
    if not q:
        return "FEHLER: leerer Tap-Text"
    try:
        import jack_xiaomi_unlock
        us = jack_xiaomi_unlock.ensure_unlocked()
        try:
            import jack_log
            jack_log.log_decision("UNLOCK", str(us)[:80], "tap_text:" + q[:40])
        except Exception:
            pass
    except Exception:
        pass
    try:
        from jack_vision_selector import tap_text as _vs_tap
        ok, msg = _vs_tap(q, partial=partial)
        out = ("OK: " if ok else "FEHLER: ") + str(msg)
        try:
            import jack_log
            jack_log.log_decision("TAP_TEXT", q[:60], out[:80])
        except Exception:
            pass
        return out
    except Exception as e:
        return "FEHLER tap_text: " + str(e)[:200]

def run(cmd, timeout=120):
    ok, msg = pruefe(cmd)
    if not ok:
        return msg
    # High-level UI: kein Shell, sondern vision_selector
    _c = (cmd or "").strip()
    _cl = _c.lower()
    if _cl.startswith("tap_text:") or _cl.startswith("tap:"):
        return tap_text(_c.split(":", 1)[1].strip())
    # Xiaomi UI-Befehle: Screen vorher entsperren (Qwen 21.08.)
    _ui = ('monkey', 'am start', 'input ', 'uiautomator')
    if 'xiaomi-jack' in cmd and any(u in cmd for u in _ui):
        try:
            import jack_xiaomi_unlock
            _us = jack_xiaomi_unlock.ensure_unlocked()
            import jack_log; jack_log.log_decision('UNLOCK', _us, cmd[:60])
        except Exception:
            pass
    try:
        r = subprocess.run(['bash','-lc',cmd], capture_output=True,
                           text=True, timeout=timeout,
                           cwd=os.path.expanduser('~/jack'))
        out = (r.stdout or '') + (r.stderr or '')
        out = out.strip() or '(kein Output)'
        rc = r.returncode
        try:
            import jack_observer
            obs_ok, errs = jack_observer.check_output(r.stdout or '', r.stderr or '')
            if not obs_ok and rc == 0:
                rc = 99
                out = '[OBSERVER BLOCK] OS luegt mit rc=0! Fehler: ' + str(errs) + '\n\n' + out
        except Exception:
            pass
        if len(out) > 3000:
            out = out[:1500] + chr(10) + '...' + chr(10) + out[-1200:]
        try:
            import jack_log; jack_log.log_decision('EXEC', cmd[:80], 'rc=' + str(rc))
        except Exception: pass
        # Outcome-Tracking: Befehl + Ergebnis speichern (Qwen 21.08.)
        try:
            import jack_outcome_tracker
            jack_outcome_tracker.log_outcome(cmd[:500], rc, out[:1000])
        except Exception:
            pass
        return 'rc=' + str(rc) + chr(10) + out
    except subprocess.TimeoutExpired:
        return 'TIMEOUT nach ' + str(timeout) + 's'
    except Exception as e:
        return 'Fehler: ' + str(e)[:200]


def handle_ui_intent(text):
    """Sprache/Text -> UI. Kurz, timeout-hart, kein Hänger."""
    import os, re, urllib.parse, subprocess
    raw = (text or "").strip()
    if not raw:
        return None
    low = raw.lower()

    def _ssh_su(inner, timeout=12):
        """Ein SSH-su, harter Timeout, kein bash -lc Umweg."""
        env = os.environ.copy()
        env["HOME"] = "/data/data/com.termux/files/home"
        cmd = [
            "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
            "-o", "ServerAliveInterval=3", "-o", "ServerAliveCountMax=2",
            "xiaomi-jack", "su", "-c", inner,
        ]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
            out = ((r.stdout or "") + (r.stderr or "")).strip()
            return r.returncode, out[:500]
        except subprocess.TimeoutExpired:
            return 124, "TIMEOUT %ss" % timeout
        except Exception as e:
            return 1, str(e)[:200]

    # Kill
    if any(w in low for w in ("stopp", "stop", "kill", "abbruch", "hör auf", "hoer auf")):
        kill = "/data/data/com.termux/files/home/jack/.jack_ui_kill"
        flag = "/data/data/com.termux/files/home/jack/.jack_ui_run"
        open(kill, "w").write("1")
        if os.path.isfile(flag):
            try: os.remove(flag)
            except Exception: pass
        return "KILL: UI/Forschung gestoppt."

    # Forschen / Suchen
    if any(w in low for w in ("forsch", "recherch", "google", "such nach", "suche nach", "such dir", "interessiert")):
        topic = raw
        for sep in ("suche nach", "such nach", "forsch nach", "recherchiere", "forsche", "google"):
            if sep in low:
                topic = raw[low.find(sep) + len(sep):].strip(" .,!")
                break
        if not topic or len(topic) < 2:
            topic = "Ollama Termux"
        flag = "/data/data/com.termux/files/home/jack/.jack_ui_run"
        kill = "/data/data/com.termux/files/home/jack/.jack_ui_kill"
        if os.path.isfile(kill):
            try: os.remove(kill)
            except Exception: pass
        open(flag, "w").write(topic)
        url = "https://www.google.com/search?q=" + urllib.parse.quote(topic)
        # 1) wecken kurz
        _ssh_su("input keyevent 224", timeout=6)
        # 2) Chrome + URL (am start bringt bestehenden Task nach vorn — kein Monkey)
        inner = "am start -a android.intent.action.VIEW -d %s -n com.android.chrome/com.google.android.apps.chrome.Main" % repr(url)
        rc, out = _ssh_su(inner, timeout=10)
        # rc 0 oder Activity already running = ok
        ok = rc in (0, 124) or "Starting: Intent" in out or "already" in out.lower()
        return "Forschung: %s\nrc=%s ok=%s\n%s\nStop: STOPP oder /kill" % (topic, rc, ok, out[:300])

    # Tippen
    m = re.search(r"(?:tippe?|klicke?|dr[uü]cke?)\s+(?:auf\s+)?(.+)$", low)
    if m:
        q = raw[m.start(1):].strip()
        return tap_text(q)

    # Nur Chrome
    if "chrome" in low and any(w in low for w in ("öffne", "oeffne", "open", "start")):
        if not any(w in low for w in ("forsch", "such", "recherch")):
            _ssh_su("input keyevent 224", timeout=6)
            rc, out = _ssh_su(
                "am start -n com.android.chrome/com.google.android.apps.chrome.Main",
                timeout=10,
            )
            return "Chrome rc=%s\n%s" % (rc, out[:300])
    return None


def extrahiere(text):
    O='[[EXEC]]'
    C='[[/EXEC]]'
    i=text.find(O)
    j=text.rfind(C)
    if i<0 or j<0 or j<=i: return None
    return text[i+len(O):j].strip()
