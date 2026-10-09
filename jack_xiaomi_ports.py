# JACK_TUNE_XPORTS: Wachposten fuer offene Ports auf dem Xiaomi (nur melden, nichts aendern)
import json, os, re, time
_ST = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".xiaomi_ports_state.json")
_WATCH = {"python", "python3", "node", "nc", "ncat", "cloudflared", "php", "ruby", "socat"}
_ERLAUBT = {("sshd", 8022), ("adbd", 5555)}
_RX = re.compile(r"^(?:tcp6?)\s+\d+\s+\d+\s+(\S+):(\d+)\s+\S+\s+LISTEN\s+(\d+)/(\S+)")

def parse(text):
    """Liefert Liste (proc, port) fuer alle auf 0.0.0.0/:::/* lauschenden Prozesse."""
    out = []
    for ln in (text or "").splitlines():
        mm = _RX.match(ln.strip())
        if not mm:
            continue
        addr, port, _pid, proc = mm.group(1), int(mm.group(2)), mm.group(3), mm.group(4)
        if addr in ("0.0.0.0", "::", ":::", "*"):
            out.append((proc.lower(), port))
    return out

def finde(eintraege):
    return [(p, port) for (p, port) in eintraege
            if p in _WATCH and (p, port) not in _ERLAUBT]

def check():
    try:
        import jack_xiaomi as _jx
        r = _jx.run_shell("netstat -tlnp 2>/dev/null", as_root=True, timeout=15)
        if not r.get("success"):
            return None
        bad = finde(parse(r.get("stdout")))
        if not bad:
            return []
        try:
            st = json.load(open(_ST))
        except Exception:
            st = {}
        now = time.time()
        neu = [b for b in bad if now - st.get("%s:%s" % b, 0) > 6 * 3600]
        if neu:
            for b in neu:
                st["%s:%s" % b] = now
            tmp = _ST + ".tmp"
            json.dump(st, open(tmp, "w"))
            os.replace(tmp, _ST)
            txt = "XIAOMI-Wachposten: unbekannter Listener auf 0.0.0.0: " + ", ".join("%s:%s" % b for b in neu)
            try:
                import jack_telegram as _tg
                _tg.send(txt)
            except Exception:
                pass
            try:
                import jack_log
                jack_log.log_decision("XPORTS", txt[:150])
            except Exception:
                pass
        return bad
    except Exception:
        return None
