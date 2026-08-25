#!/usr/bin/env python3
"""TUEV v7: Slash-Handler plus Chat-Kanal (Selfsee, Knopfe, kein ADB-Heal-Prefix)."""
import os, re, sys
sys.path.insert(0, "/data/data/com.termux/files/home/jack")
J = "/data/data/com.termux/files/home/jack"
TG = os.path.join(J, "jack_telegram.py")
TK = os.path.join(J, "jack_talk.py")
SS = os.path.join(J, "jack_selfsee.py")
tg = open(TG, encoding="utf-8", errors="ignore").read()
tk = open(TK, encoding="utf-8", errors="ignore").read() if os.path.isfile(TK) else ""
ss = open(SS, encoding="utf-8", errors="ignore").read() if os.path.isfile(SS) else ""
fast_cmds = set()
m = re.search(r"FAST_CMDS\s*=\s*\{([^}]+)\}", tg)
if m:
    fast_cmds.update(re.findall(r"'(/[^']+)'", m.group(1)))
cmds = set(fast_cmds)
cmds.update("/" + c for c in re.findall(r"_rt\s*==\s*'/([a-z_]+)'", tg))
cmds.update("/" + c for c in re.findall(r"text\.strip\(\)\s*==\s*'/([a-z_]+)'", tg))
for list_match in re.finditer(r"\[([^\]]+)\]", tg):
    cmds.update(re.findall(r"'(/[^']+)'", list_match.group(1)))
def has_handler(cmd):
    n = cmd.lstrip("/")
    if cmd in fast_cmds:
        return True
    pats = ["_rt == '%s'"%cmd, "text.strip()=='%s'"%cmd, "text.strip() == '%s'"%cmd, "'%s' in FAST_CMDS"%cmd]
    return any(p in tg for p in pats)
base = set()
for cmd in cmds:
    if cmd.startswith("/"):
        base.add(cmd.split()[0])
print("TUEV v7 SLASH")
print("="*66)
ok_s = 0
fehlt = []
for cmd in sorted(base):
    h = has_handler(cmd)
    st = "OK" if h else "HANDLER-FEHLT"
    if h: ok_s += 1
    else: fehlt.append(cmd)
    print("%-18s | %s" % (cmd, st))
print("SLASH OK: %s/%s" % (ok_s, len(base)))
if fehlt:
    print("FEHLT: " + ", ".join(fehlt[:20]))
print()
print("TUEV v7 CHAT-KANAL")
print("="*66)
checks = []
checks.append(("selfsee_go in telegram", "selfsee_go" in tg))
checks.append(("send_keyboard vor return None", "send_keyboard(_ss.handle(text)" in tg))
checks.append(("alarm nicht vor selfsee", "signal.alarm(15)" not in tg.split("elif _ss.wants(text):")[0][-400:] if "elif _ss.wants(text):" in tg else False))
checks.append(("ADB-Heal Prefix tot", "| ADB-Heal |" not in tk))
checks.append(("ist_zustand da", "def ist_zustand" in tk))
checks.append(("persona kumpel", os.path.isfile(J+"/jack_persona.md")))
try:
    import jack_selfsee as _ss
    checks.append(("wants analysiere", _ss.wants("analysiere deinen eigenen Code")))
    checks.append(("wants smalltalk false", not _ss.wants("Hast du Lust auf Smalltalk")))
except Exception as e:
    checks.append(("selfsee import", False))
    print("import err", type(e).__name__, str(e)[:80])
fail = 0
for n, v in checks:
    print("%-32s | %s" % (n, "OK" if v else "FAIL"))
    if not v: fail += 1
print("="*66)
print("CHAT FAIL:", fail)
raise SystemExit(1 if fail or fehlt else 0)
