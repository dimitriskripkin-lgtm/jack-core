#!/usr/bin/env python3
"""jack_approval_digest.py — Sammel-Approval statt Einzelnachrichten.

Statt 300 einzelner Telegram-Nachrichten: eine Digest-Nachricht mit
allen pending Approvals + /approve_all Befehl. Kein Timeout.
"""
MODULE_VERSION = 1

import os, sys, json, time
J = os.path.expanduser("~/jack")
sys.path.insert(0, J)
from jack_log import get_logger
log = get_logger("jack_approval_digest")

APPROVALS = os.path.join(J, "pending_approvals.json")
DIGEST_STATE = os.path.join(J, "digest_last_sent.json")

def load_pending():
    try:
        data = json.load(open(APPROVALS))
        if isinstance(data, list): return data
        if isinstance(data, dict): return list(data.values())
    except Exception: pass
    return []

def last_sent_count():
    try:
        return json.load(open(DIGEST_STATE)).get("count", 0)
    except Exception: return 0

def save_sent_count(n):
    json.dump({"count": n, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}, open(DIGEST_STATE,'w'))

def send_digest():
    pending = load_pending()
    n = len(pending)
    if n == 0: return 0

    # Nur senden wenn neue Einträge dazugekommen
    last = last_sent_count()
    if n == last: return 0

    try:
        import jack_telegram as _jt  # lazy — zirkulär, bewusst

        # Sammel-Nachricht bauen
        lines = [f"🔧 *{n} Fixes bereit zur Genehmigung*\n"]
        for i, entry in enumerate(pending[:15]):  # Max 15 anzeigen
            fid = entry.get("id","?")
            fname = os.path.basename(entry.get("file","?"))
            desc = entry.get("desc", entry.get("act","fix"))[:50]
            lines.append(f"  `{i+1}.` {fname} — {desc}")
        if n > 15:
            lines.append(f"  _...und {n-15} weitere_")

        lines.append(f"\n✅ Alle genehmigen: `/approve_all`")
        lines.append(f"📋 Einzeln: `/approve_ID`")
        lines.append(f"❌ Alle ablehnen: `/reject_all`")

        msg = "\n".join(lines)
        _jt.send_message(msg)
        save_sent_count(n)
        log.info(f"Digest gesendet: {n} Fixes")
        return n
    except Exception as e:
        log.exception("Digest-Fehler", e)
        return 0

def run():
    return send_digest()

if __name__ == "__main__":
    n = run()
    print(f"Digest: {n} Fixes gemeldet")
