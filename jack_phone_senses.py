#!/usr/bin/env python3
"""jack_phone_senses.py - Phone-Haende Phase 2: Sinne (L0, nur lesen) fuer den HONOR. Kap 278.

Grundlage: ARBEITSPLATZ/gemeinsam/phone/entwurf_sicherheitsrahmen.md (Fassung 2, Review bestanden, Go Dima 11.10.2026).
Nur feste, lesende rish-Befehle. Kein freier Shell-Zugang, kein Text aus Agenten in Befehlen, keine Wirkung auf das Geraet.
Vor jedem Sinn: Not-Aus -> Shizuku -> Display/Sperre -> Vordergrund -> Tabu/Erlaubnisliste.
Inhalte (UI-Text, Benachrichtigungstexte) verlassen nie die rish-Shell: dort wird nur gezaehlt bzw. nur Paketnamen gefiltert.
Audit: ~/jack/logs/phone_audit.log (600, nur anhaengen, eigene Rotation 1 MiB / 14 Tage), nie Inhalte.

Aufruf: python3 jack_phone_senses.py status | selftest
"""
import json
import os
import re
import subprocess
import sys
import time

VERSION = "1"
HOME = os.path.expanduser("~")
KILL = os.path.join(HOME, "jack", ".phone_off")
AUDIT = os.path.join(HOME, "jack", "logs", "phone_audit.log")
AUDIT_MAX = 1024 * 1024
AUDIT_DAYS = 14
STEP_TIMEOUT = 10

# Live verifiziert 11.10.2026 (pm list packages)
SETTINGS, TERMUX, LAUNCHER, SYSTEMUI = "com.android.settings", "com.termux", "com.hihonor.android.launcher", "com.android.systemui"
ALLOW_FG = {SETTINGS, TERMUX, LAUNCHER, SYSTEMUI}
TABU = {
    "com.entersekt.authapp.sparkasse", "com.bitpanda.bitpanda", "com.coinmarketcap.android",
    "com.authenticator.authservice2", "com.azure.authenticator", "com.google.android.apps.authenticator2",
    "org.telegram.messenger", "com.facebook.katana", "com.facebook.orca", "com.facebook.stella",
    "com.ebay.mobile", "com.ebay.kleinanzeigen", "com.google.android.contacts", "com.google.android.apps.photos",
    "com.google.android.dialer", "com.android.vending", "com.anthropic.claude", "ai.x.grok", "ai.x.grok.bot",
    "ai.qwenlm.chat.android", "ai.perplexity.app.android", "com.deepseek.chat", "com.codeway.chatapp",
    # live nachgezogen 11.10.2026
    "com.google.android.gm", "com.google.android.apps.messaging", "com.paypal.android.p2pmobile",
    "moe.shizuku.privileged.api", "org.mozilla.firefox", "com.google.android.apps.walletnfcrel",
    "com.openai.chatgpt", "com.android.chrome", "com.whatsapp",
}
PKG_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+$")

# Feste Befehle. Filterung/Zaehlung passiert IN der rish-Shell, damit keine Inhalte in diesen Prozess kommen.
CMD = {
    "id": "id",
    "focus": "dumpsys window | grep -E 'mCurrentFocus=' | head -1",
    "wake": "dumpsys power | grep -E 'mWakefulness=' | head -1",
    "keyguard": "dumpsys window | grep -E 'isKeyguardShowing=' | head -1",
    "battery": "dumpsys battery | grep -E '^  (level|temperature|status|AC powered|USB powered):'",
    "notif": "dumpsys notification | grep -oE 'NotificationRecord\\([^ ]+ pkg=[A-Za-z0-9_.]+' | grep -oE 'pkg=[A-Za-z0-9_.]+'",
    "ui": "uiautomator dump /proc/self/fd/1 2>/dev/null | grep -oE '<node |package=\"[A-Za-z0-9_.]+\"' | sort | uniq -c",
}


class Stop(Exception):
    def __init__(self, result, reason, fg="-"):
        super().__init__(reason)
        self.result, self.reason, self.fg = result, reason, fg


def _rish_real(key):
    # rish schreibt die Ausgabe zufaellig auf stdout ODER stderr (gemessen 11.10.2026: ~40 % auf stderr) -> zusammenlegen
    p = subprocess.run(["rish", "-c", CMD[key]], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                       timeout=STEP_TIMEOUT, text=True)
    return p.returncode, p.stdout[:20000]


RISH = _rish_real  # im Selbsttest ersetzt


def audit(job, step, action, fg_before, fg_after, result, reason):
    os.makedirs(os.path.dirname(AUDIT), exist_ok=True)
    _rotate()
    line = json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "auftrag": job, "schritt": step, "aktion": action,
                       "fg_vor": fg_before, "fg_nach": fg_after, "ergebnis": result, "grund": reason[:80]}, ensure_ascii=False)
    fd = os.open(AUDIT, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        os.write(fd, (line + "\n").encode())
    finally:
        os.close(fd)
    os.chmod(AUDIT, 0o600)


def _rotate():
    """Eigene Rotation (jack_logrot greift erst ab 5 MiB): Zeilen aelter als 14 Tage weg, max 1 MiB (aelteste zuerst)."""
    if not os.path.exists(AUDIT):
        return
    size = os.path.getsize(AUDIT)
    cutoff = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - AUDIT_DAYS * 86400))
    with open(AUDIT, encoding="utf-8", errors="replace") as f:
        first = f.readline()
    if size < AUDIT_MAX * 0.9 and first[8:27] >= cutoff:
        return
    with open(AUDIT, encoding="utf-8", errors="replace") as f:
        lines = [l for l in f if l[8:27] >= cutoff]
    while lines and sum(len(l.encode()) for l in lines) > AUDIT_MAX * 0.7:
        lines = lines[len(lines) // 10 + 1:]
    tmp = AUDIT + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.writelines(lines)
    os.replace(tmp, AUDIT)


def _run(key):
    try:
        rc, out = RISH(key)
    except subprocess.TimeoutExpired:
        raise Stop("TIMEOUT", "rish_%s_timeout" % key)
    except OSError:
        raise Stop("ABORTED", "rish_fehlt")
    if rc != 0 and key in ("id", "focus", "wake", "keyguard"):
        raise Stop("ABORTED", "rish_%s_rc%d" % (key, rc))
    return out


def foreground_pkg():
    out = _run("focus")
    m = re.search(r"\bu\d+ ([A-Za-z0-9_.]+)/", out)
    if not m or not PKG_RE.match(m.group(1)):
        raise Stop("ABORTED", "vordergrund_unklar")
    return m.group(1)


def guard(need_allow):
    """Entscheidungsregel Abschnitt 2. Liefert das Vordergrund-Paket oder wirft Stop."""
    if os.path.exists(KILL):
        raise Stop("BLOCKED", "phone_off")
    if "uid=2000" not in _run("id"):
        raise Stop("ABORTED", "shizuku_nicht_shell")
    if "mWakefulness=Awake" not in _run("wake"):
        raise Stop("ABORTED", "display_aus")
    if "isKeyguardShowing=false" not in _run("keyguard"):
        raise Stop("ABORTED", "gesperrt")
    fg = foreground_pkg()
    if fg in TABU:
        raise Stop("ABORTED", "tabu_app", fg)
    if need_allow and fg not in ALLOW_FG:
        raise Stop("BLOCKED", "vordergrund_nicht_erlaubt", fg)
    return fg


def sense(name, job=None, step=1):
    """Ein Sinn mit Pruefung vorher und nachher. Rueckgabe dict mit ergebnis und daten (nie Inhalte)."""
    job = job or "L0-" + time.strftime("%Y%m%d%H%M%S")
    fg = "-"
    try:
        need_allow = name in ("ui_summary",)
        fg = guard(need_allow)
        if name == "foreground":
            data = {"paket": fg, "erlaubt": fg in ALLOW_FG}
        elif name == "battery":
            vals = dict(re.findall(r"^\s*([A-Za-z ]+):\s*(\S+)", _run("battery"), re.M))
            data = {"level": int(vals.get("level", -1)), "temp_c": int(vals.get("temperature", 0)) / 10,
                    "status": vals.get("status"), "ac": vals.get("AC powered"), "usb": vals.get("USB powered")}
        elif name == "notif_meta":
            pk = re.findall(r"pkg=([A-Za-z0-9_.]+)", _run("notif"))
            cnt = {}
            for p in pk:
                if PKG_RE.match(p):
                    cnt[p] = cnt.get(p, 0) + 1
            data = {"anzahl": sum(cnt.values()), "pakete": cnt}
        elif name == "ui_summary":
            if fg == SYSTEMUI:
                raise Stop("BLOCKED", "systemui_kein_ui", fg)  # Auflage Fassung 2 (H-D)
            out = _run("ui")
            nodes = sum(int(n) for n in re.findall(r"^\s*(\d+) <node", out, re.M))
            pk = {p: int(n) for n, p in re.findall(r'^\s*(\d+) package="([A-Za-z0-9_.]+)"', out, re.M)}
            if any(p in TABU for p in pk):
                raise Stop("ABORTED", "tabu_im_ui", fg)
            data = {"paket": fg, "elemente": nodes, "pakete": sorted(pk)}
        else:
            raise Stop("BLOCKED", "sinn_unbekannt", fg)
        fg_after = foreground_pkg()
        if fg_after != fg:
            raise Stop("ABORTED", "vordergrund_gewechselt", fg)
        audit(job, step, name, fg, fg_after, "OK", "ok")
        return {"ergebnis": "OK", "daten": data}
    except Stop as e:
        audit(job, step, name, e.fg if e.fg != "-" else fg, "-", e.result, e.reason)
        return {"ergebnis": e.result, "grund": e.reason}


def status():
    job = "L0-" + time.strftime("%Y%m%d%H%M%S")
    out = {}
    for i, n in enumerate(("foreground", "battery", "notif_meta", "ui_summary"), 1):
        out[n] = sense(n, job, i)
    return out


# ------------------------------------------------------------ Selbsttest (ohne Geraet, gefaelschtes rish)
def selftest():
    global RISH, KILL, AUDIT
    import tempfile
    tmp = tempfile.mkdtemp(prefix="phone_st_")
    KILL, AUDIT = os.path.join(tmp, ".phone_off"), os.path.join(tmp, "logs", "phone_audit.log")
    state = {}

    def fake(key):
        s = state
        if s.get("norish"):
            raise OSError("weg")
        return {"id": (0, "uid=%s(shell)" % s.get("uid", 2000)),
                "focus": (0, "  mCurrentFocus=Window{abc u0 %s/%s.Main}" % (s["fg"], s["fg"])),
                "wake": (0, "  mWakefulness=%s" % s.get("wake", "Awake")),
                "keyguard": (0, "    isKeyguardShowing=%s" % s.get("kg", "false")),
                "battery": (0, "  AC powered: false\n  USB powered: true\n  status: 2\n  level: 77\n  temperature: 312\n"),
                "notif": (0, "pkg=com.whatsapp\npkg=com.whatsapp\npkg=com.android.settings\n"),
                "ui": (0, "     45 <node \n     45 package=\"%s\"\n" % s.get("uipkg", s["fg"]))}[key]
    RISH = fake
    cases = [
        ("Normal Termux", {"fg": TERMUX}, "ui_summary", "OK", None),  # erwartet elemente=45
        ("H-B Tabu-App (Claude)", {"fg": "com.anthropic.claude"}, "ui_summary", "ABORTED", "tabu_app"),
        ("Tabu auch fuer foreground", {"fg": "org.telegram.messenger"}, "foreground", "ABORTED", "tabu_app"),
        ("unbekannte App", {"fg": "com.example.spiel"}, "ui_summary", "BLOCKED", "vordergrund_nicht_erlaubt"),
        ("unbekannte App nur Paketname", {"fg": "com.example.spiel"}, "foreground", "OK", None),
        ("H-D SystemUI kein UI", {"fg": SYSTEMUI}, "ui_summary", "BLOCKED", "systemui_kein_ui"),
        ("Display aus", {"fg": TERMUX, "wake": "Asleep"}, "battery", "ABORTED", "display_aus"),
        ("gesperrt", {"fg": TERMUX, "kg": "true"}, "battery", "ABORTED", "gesperrt"),
        ("Shizuku falsche uid", {"fg": TERMUX, "uid": 10400}, "battery", "ABORTED", "shizuku_nicht_shell"),
        ("rish fehlt", {"fg": TERMUX, "norish": True}, "battery", "ABORTED", "rish_fehlt"),
        ("Tabu im UI-Baum", {"fg": SETTINGS, "uipkg": "com.whatsapp"}, "ui_summary", "ABORTED", "tabu_im_ui"),
        ("Benachrichtigungen nur Pakete", {"fg": LAUNCHER}, "notif_meta", "OK", None),
        ("unbekannter Sinn", {"fg": TERMUX}, "shell", "BLOCKED", "sinn_unbekannt"),
    ]
    ok = 0
    for name, st, s, want, why in cases:
        state.clear(); state.update(st)
        r = sense(s, "TEST", 1)
        good = r["ergebnis"] == want and (why is None or r.get("grund") == why)
        ok += good
        print("%-32s %s  %s" % (name, "ok" if good else "FEHLER", json.dumps(r, ensure_ascii=False)[:110]))
    # H-C Not-Aus
    open(KILL, "w").close()
    state.clear(); state.update({"fg": TERMUX})
    r = sense("battery", "TEST", 1)
    good = r == {"ergebnis": "BLOCKED", "grund": "phone_off"}
    ok += good
    print("%-32s %s  %s" % ("H-C Not-Aus", "ok" if good else "FEHLER", r))
    os.remove(KILL)
    # Audit: Rechte 600, keine Inhalte, Rotation
    mode = oct(os.stat(AUDIT).st_mode & 0o777)
    txt = open(AUDIT).read()
    good = mode == "0o600" and "whatsapp" not in txt and "level" not in txt and "elemente" not in txt
    ok += good
    print("%-32s %s  rechte=%s zeilen=%d" % ("Audit 600, ohne Inhalte", "ok" if good else "FEHLER", mode, txt.count("\n")))
    with open(AUDIT, "a") as f:
        f.write(json.dumps({"ts": "2020-01-01 00:00:00", "aktion": "alt"}) + "\n")
        f.write(("x" * 1000 + "\n") * 1200)
    state.clear(); state.update({"fg": TERMUX})
    sense("foreground", "TEST", 1)
    good = os.path.getsize(AUDIT) < AUDIT_MAX and "2020-01-01" not in open(AUDIT).read()
    ok += good
    print("%-32s %s  groesse=%d" % ("Audit-Rotation 1 MiB/14 Tage", "ok" if good else "FEHLER", os.path.getsize(AUDIT)))
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    total = len(cases) + 3
    print("PHONE-SINNE-SELFTEST %d/%d ok (v%s)" % (ok, total, VERSION))
    return ok == total


def main(argv):
    if len(argv) >= 2 and argv[1] == "selftest":
        return 0 if selftest() else 1
    if len(argv) >= 2 and argv[1] == "status":
        print(json.dumps(status(), ensure_ascii=False, indent=1))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
