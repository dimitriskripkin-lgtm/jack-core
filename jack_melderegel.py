#!/usr/bin/env python3
"""Auftrag M2: lesende, deterministische JACK-Meldungsentscheidung (OFFLINE)."""
import hashlib
import json
from pathlib import Path
import re
import time

HOME = Path("/data/data/com.termux/files/home/jack")
CONFIG = HOME / "jack_melderegeln.json"
KLASSEN = {"SOFORT", "PUFFER", "NUR_LOG"}


def _normal(text):
    s = str(text or "").casefold()
    # Zahlenwerte, Uhrzeiten, Akkustaende und IPs normalisieren.
    s = re.sub(r"\d+(?:[.,:]\d+)*", "#", s)
    return " ".join(s.split())


def _finger(text, quelle, gruppe=""):
    basis = str(gruppe or _normal(text))
    q = re.sub(r"[^a-z0-9_:-]", "_", str(quelle or "system").lower())[:36]
    return q + ":" + hashlib.sha256(basis.encode("utf-8")).hexdigest()[:20]


def lade_regeln(pfad=CONFIG):
    """Konfigurationsfehler signalisieren, nicht aus undefinierten Regeln filtern."""
    obj = json.loads(Path(pfad).read_text(encoding="utf-8"))
    if not isinstance(obj, dict) or not isinstance(obj.get("regeln"), list):
        raise ValueError("MELDEREGELN_UNGUELTIG")
    return obj


def klassifiziere(text, quelle, wichtig, gesehen=None, jetzt=None, regeln=None):
    """Pure decision: gesehen={fingerprint: timestamp}. Does NOT update state.

    NUR_LOG is permitted for explicitly noncritical types or a known repeat.
    SOFORT critical rules cannot be deduped. On unavailable config: safe fallback.
    Callers persist seen fingerprints ONLY after ACK or successful enqueue,
    and never treat an unsent message as delivered.
    """
    basis = "SOFORT" if wichtig is True else "PUFFER"
    result = {"klasse": basis, "grund": "fallback", "kritisch": bool(wichtig),
              "dedupe_s": 0, "fingerprint": _finger(text, quelle)}
    if not isinstance(text, str) or not text.strip():
        return result
    if regeln is None:
        try:
            regeln = lade_regeln()
        except (OSError, ValueError, TypeError):
            result["grund"] = "konfiguration_fehlt"
            return result
    rules = regeln.get("regeln", [])
    if not isinstance(rules, list):
        return result
    found = None
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        if rule.get("quelle") and rule["quelle"] != quelle:
            continue
        try:
            if re.search(rule["muster"], text, re.I):
                found = rule
                break
        except (re.error, KeyError, TypeError):
            continue
    if found is None:
        return result
    klass = found.get("klasse")
    if klass not in KLASSEN:
        return result
    critical = found.get("kritisch") is True
    if critical:
        klass = "SOFORT"
    delay = found.get("dedupe_s", 0)
    if not isinstance(delay, (int, float)) or delay < 0 or delay > 604800:
        delay = 0
    key = _finger(text, quelle, "regel:" + str(found.get("id", "")))
    result = {"klasse": klass, "grund": str(found.get("id", "regel"))[:60],
              "kritisch": critical, "dedupe_s": delay, "fingerprint": key}
    if not critical and klass != "NUR_LOG" and delay > 0 and isinstance(gesehen, dict):
        stamp = gesehen.get(key)
        current = time.time() if jetzt is None else float(jetzt)
        if isinstance(stamp, (float, int)) and 0 <= current - stamp < delay:
            result["klasse"] = "NUR_LOG"
            result["grund"] += "_duplikat"
    return result


def entscheide_live(text, quelle, wichtig):
    """Read last ACKed/enqueued timestamps (no writes before send)."""
    return klassifiziere(text, quelle, wichtig, gesehen=_lade_gesehen())


def _lade_gesehen(pfad=None):
    p = Path(pfad) if pfad else HOME / "logs" / ".tg_m2_seen.json"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def quittiere(result, pfad=None):
    """Record only AFTER Telegram ACK or durable queue write.

    Uses a dedicated lock (never the tg_send _record lock), so no recursive
    flock deadlock. Corrupt state fails open (can repeat) rather than lose alerts.
    """
    if not isinstance(result, dict) or result.get("kritisch"):
        return False
    if result.get("klasse") not in ("SOFORT", "PUFFER"):
        return False
    if not result.get("dedupe_s") or not result.get("fingerprint"):
        return False
    import fcntl
    import os
    p = Path(pfad) if pfad else HOME / "logs" / ".tg_m2_seen.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    lock = p.with_suffix(".lock")
    fd = os.open(lock, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        seen = _lade_gesehen(p)
        now = time.time()
        seen = {str(k):v for k,v in seen.items()
                if isinstance(v,(float,int)) and 0 <= now-v <= 604800}
        seen[result["fingerprint"]] = now
        # Bounded by one week's still-useful fingerprints.
        if len(seen) > 2000:
            seen = dict(sorted(seen.items(), key=lambda z:z[1])[-2000:])
        tmp = p.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as handle:
            os.fchmod(handle.fileno(), 0o600)
            json.dump(seen, handle, separators=(",", ":"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, p)
        return True
    except (OSError, ValueError, TypeError):
        return False
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
