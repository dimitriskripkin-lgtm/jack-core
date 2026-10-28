#!/usr/bin/env python3
"""JACK_TUNE_FAHRTLAGE (28.10.2026, Claude, Kap 308, Dima-Go 13:06): Lagebild fuer Grok-Bot/Tesla.
Schreibt ~/jack-gedaechtnis/lage/aktuell.md (PRIVATES Repo dimitriskripkin-lgtm/jack-gedaechtnis) und pusht.
Weg: Grok-Bot liest die Datei -> steht in seinem Verlauf -> Tesla-Grok findet sie ("guck bei Jack", Test 28.10. 13:12 bestanden).
NUR LESEN auf Honor/Xiaomi. Inhalt: Zahlen und Zustaende, KEINE Geheimnisse, keine Chat-/Benachrichtigungstexte.
Aufruf: python3 jack_fahrtlage.py [--kein-push]
"""
import os, sys, glob, time, subprocess, datetime
J = "/data/data/com.termux/files/home/jack"
G = "/data/data/com.termux/files/home/jack-gedaechtnis"
SV = "/data/data/com.termux/files/usr/var/service"
KERN = ["jack_telegram", "jack_waechter", "jack_missions", "jack_mcp", "jack_cortex", "jack_autolearn",
        "jack_publisher", "jack_focus_monitor", "jack_honor_watch", "cloudflared", "crond"]
sys.path.insert(0, J)


def sh(cmd, t=15):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=t,
                           env=dict(os.environ, SVDIR=SV), stdin=subprocess.DEVNULL)
        return r.stdout.strip()
    except Exception:
        return ""


def dienste():
    tot = [d for d in KERN if not sh("sv status " + d).startswith("run:")]
    return len(KERN) - len(tot), tot


def honor():
    try:
        import jack_lagebild as L
        h = L.honor()
        return h.get("akku"), h.get("temp_c")
    except Exception:
        return None, None


def xiaomi():
    try:
        import jack_xiaomi as X
        c = ("export SVDIR=/data/data/com.termux/files/usr/var/service PATH=/data/data/com.termux/files/usr/bin:$PATH; "
             "for z in /sys/class/thermal/thermal_zone*/temp; do cat $z 2>/dev/null; done | sort -n | tail -1; "
             "sv status n8n 2>&1 | cut -c1-4")
        r = X.run_shell("/data/data/com.termux/files/usr/bin/bash -s", timeout=25, as_root=False, input_data=c)
        z = (r.get("stdout", "") if isinstance(r, dict) else "").split()
        temp = round(int(z[0]) / 1000, 1) if z and z[0].isdigit() else None
        return True, temp, ("laeuft" if "run:" in " ".join(z) else "aus")
    except Exception:
        return False, None, "?"


def playlist():
    try:
        z = open(J + "/logs/musik_gut.log").read().strip().splitlines()[-1]
        s = z.split("stand", 1)[1].split("|")[0].strip()
        return s
    except Exception:
        return "?"


def fails24():
    g = time.time() - 86400
    return sum(1 for f in glob.glob(J + "/missions/fail/*.json") if os.path.getmtime(f) > g)


def offen():
    try:
        return open(G + "/entscheidungen/offen.md").read().strip()
    except Exception:
        return "(keine Datei)"


def main():
    jetzt = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    n_ok, tot = dienste()
    akku, htemp = honor()
    xok, xtemp, n8n = xiaomi()
    t = [f"# JACK Lage {jetzt} (Bremen)", "",
         "Kurzfassung fuer Tesla: lies die Punkte vor, hoechstens zwei Saetze pro Punkt.", "",
         f"- JACK-Dienste: {n_ok} von {len(KERN)} laufen" + (f", AUS: {', '.join(tot)}" if tot else ", alles gruen"),
         f"- Honor: Akku {akku if akku is not None else '?'} %, {htemp if htemp is not None else '?'} Grad",
         f"- Xiaomi: {'erreichbar' if xok else 'NICHT erreichbar'}, {xtemp if xtemp is not None else '?'} Grad, n8n {n8n}",
         f"- Fehlgeschlagene JACK-Auftraege letzte 24 h: {fails24()}",
         f"- Playlist-Rettung Musik gut: {playlist()} Songs",
         "", "## Offene Entscheidungen fuer Dima", offen(), "",
         "_Automatisch von JACK (Honor). Wahrheit ist das Honor, diese Datei ist nur ein Spiegel._", ""]
    os.makedirs(G + "/lage", exist_ok=True)
    p = G + "/lage/aktuell.md"
    open(p, "w").write("\n".join(t))
    print("\n".join(t[:9]))
    if "--kein-push" not in sys.argv:
        out = sh(f"cd {G} && git add lage/aktuell.md && git commit -q -m 'Lage {jetzt}' && timeout 60 git push -q origin HEAD 2>&1 | tail -2; git log --oneline -1", 90)
        print("push:", out)


if __name__ == "__main__":
    main()
