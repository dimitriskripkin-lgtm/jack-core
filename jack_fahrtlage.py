#!/usr/bin/env python3
"""JACK_TUNE_FAHRTLAGE (28.10.2026, Claude, Kap 308, Dima-Go 13:06 + 14:22): Lagebild + Grok-Briefkasten.
1) Schreibt ~/jack-gedaechtnis/lage/aktuell.md (PRIVATES Repo dimitriskripkin-lgtm/jack-gedaechtnis) und pusht.
2) Liest auftraege/*.md (von Grok, nur NEUE Dateien), meldet sie Dima per Telegram (frage/vorschlag mit Ja/Nein-Knopf,
   hinweis ohne Knopf). Antwort per Knopf -> status/<id>.json, commit + push. JACK FUEHRT NICHTS AUS (kein Befehlsbus).
NUR LESEN auf Honor/Xiaomi. Keine Geheimnisse, keine Chat-/Benachrichtigungstexte.
Aufruf: python3 jack_fahrtlage.py [--kein-push]
"""
import os, re, sys, glob, json, time, fcntl, secrets, subprocess, datetime
from contextlib import contextmanager
J = "/data/data/com.termux/files/home/jack"
G = "/data/data/com.termux/files/home/jack-gedaechtnis"
SV = "/data/data/com.termux/files/usr/var/service"
PEND = J + "/logs/grok_pending.json"
KERN = ["jack_telegram", "jack_waechter", "jack_missions", "jack_mcp", "jack_cortex", "jack_autolearn",
        "jack_publisher", "jack_focus_monitor", "jack_honor_watch", "cloudflared", "crond"]
TYPEN = ("frage", "hinweis", "vorschlag")
ID_RX = re.compile(r"^[A-Za-z0-9_-]{3,60}$")
MAX_PRO_LAUF = 3
TTL = 48 * 3600
sys.path.insert(0, J)


def sh(cmd, t=15):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=t,
                           env=dict(os.environ, SVDIR=SV), stdin=subprocess.DEVNULL)
        return r.stdout.strip()
    except Exception:
        return ""


@contextmanager
def _lock(pfad):
    fd = os.open(pfad, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def git_sync(msg, dateien, push=True):
    """Ein Lock fuer alle Git-Schritte (Cron und Telegram-Knopf), erst pull (Grok schreibt auch), dann commit/push."""
    with _lock(J + "/logs/.gedaechtnis_git.lock"):
        sh(f"cd {G} && timeout 60 git pull -q --rebase --autostash origin HEAD", 90)
        if not dateien:
            return ""
        q = " ".join("'" + d.replace("'", "") + "'" for d in dateien)
        m = re.sub(r"[^\w .:-]", "", msg)[:80]
        out = sh(f"cd {G} && git add -- {q} && git commit -q -m '{m}' -- {q} >/dev/null 2>&1; "
                 + ("timeout 60 git push -q origin HEAD 2>&1 | tail -2; " if push else "") + "git log --oneline -1", 120)
        return out


# ---------- Lagebild ----------
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
        return z.split("stand", 1)[1].split("|")[0].strip()
    except Exception:
        return "?"


def fails24():
    g = time.time() - 86400
    acts = {}
    for f in glob.glob(J + "/missions/fail/*.json"):
        if os.path.getmtime(f) <= g:
            continue
        try:
            a = str(json.load(open(f)).get("act") or "?")
        except Exception:
            a = "?"
        acts[a] = acts.get(a, 0) + 1
    return sum(acts.values()), ", ".join(f"{k} x{v}" for k, v in sorted(acts.items(), key=lambda x: -x[1]))


def offen():
    try:
        return open(G + "/entscheidungen/offen.md").read().strip()
    except Exception:
        return "(keine Datei)"


# ---------- Grok-Briefkasten ----------
def _auftrag_lesen(pfad):
    d = {}
    try:
        for z in open(pfad, encoding="utf-8", errors="replace").read().splitlines()[:20]:
            if ":" in z:
                k, v = z.split(":", 1)
                k = k.strip().lower().lstrip("-* ")
                if k in ("typ", "text") and k not in d:
                    d[k] = v.strip()
    except OSError:
        return None
    typ = d.get("typ", "").lower()
    text = re.sub(r"[\x00-\x1f\x7f]", " ", d.get("text", "")).strip()[:500]
    if typ not in TYPEN or len(text) < 3:
        return None
    return typ, text


def _status_pfad(aid):
    return f"{G}/status/{aid}.json"


def _pend_laden():
    try:
        return json.load(open(PEND))
    except Exception:
        return {}


def _pend_speichern(d):
    tmp = PEND + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(d, f)
    os.replace(tmp, PEND)


def briefkasten(senden=True):
    """Neue Grok-Auftraege melden. Gibt (neu_gemeldet, offen_gesamt, geaenderte_dateien) zurueck."""
    os.makedirs(G + "/status", exist_ok=True)
    neu, geaendert, offen_n = 0, [], 0
    for p in sorted(glob.glob(G + "/auftraege/*.md")):
        aid = os.path.basename(p)[:-3]
        if not ID_RX.match(aid):
            continue
        sp = _status_pfad(aid)
        if os.path.exists(sp):
            try:
                if json.load(open(sp)).get("antwort") is None:
                    offen_n += 1
            except Exception:
                pass
            continue
        a = _auftrag_lesen(p)
        st = {"id": aid, "gemeldet": datetime.datetime.now().isoformat(timespec="seconds"), "antwort": None}
        if a is None:
            st["antwort"] = "ungueltig"
            st["grund"] = "typ nicht frage/hinweis/vorschlag oder text fehlt"
        elif neu >= MAX_PRO_LAUF or not senden:
            offen_n += 1
            continue
        else:
            typ, text = a
            if typ == "hinweis":
                import jack_tg_send
                jack_tg_send.send("Hinweis von Grok (" + aid + "):\n" + text, wichtig=False, quelle="grok_briefkasten")
                st["antwort"] = "zur_kenntnis"
            else:
                nonce = secrets.token_hex(16)
                with _lock(PEND + ".lock"):
                    d = {k: v for k, v in _pend_laden().items() if v.get("expires", 0) > time.time()}
                    d[nonce] = {"id": aid, "expires": time.time() + TTL}
                    _pend_speichern(d)
                import jack_telegram as tg
                tg.send_keyboard(("Frage" if typ == "frage" else "Vorschlag") + " von Grok (" + aid + "):\n" + text
                                 + "\n\n(Nur Antwort, JACK fuehrt nichts aus. 48 h gueltig)",
                                 [[("Ja", "ga:ja:" + nonce), ("Nein", "ga:nein:" + nonce)]])
                offen_n += 1
            neu += 1
        with open(sp, "w") as f:
            json.dump(st, f, ensure_ascii=False)
        geaendert.append("status/" + aid + ".json")
    return neu, offen_n, geaendert


def antwort(data, chat, user, trusted):
    """Telegram-Knopf ga:ja|nein:<nonce> -> status/<id>.json. Nur Dimas Privatchat, Einmal-Code."""
    m = re.fullmatch(r"ga:(ja|nein):([0-9a-f]{32})", str(data or ""))
    if not m:
        return None
    if None in (chat, user, trusted) or not (str(chat) == str(user) == str(trusted)):
        return "Grok-Frage: fremder Absender, abgelehnt"
    art, nonce = m.groups()
    with _lock(PEND + ".lock"):
        d = _pend_laden()
        item = d.pop(nonce, None)
        if item is not None:
            _pend_speichern(d)
    if not item:
        return "Grok-Frage: Knopf nicht mehr gueltig"
    if item.get("expires", 0) <= time.time():
        return "Grok-Frage: Knopf abgelaufen"
    aid = item["id"]
    sp = _status_pfad(aid)
    try:
        st = json.load(open(sp))
    except Exception:
        st = {"id": aid}
    st["antwort"] = art
    st["beantwortet"] = datetime.datetime.now().isoformat(timespec="seconds")
    with open(sp, "w") as f:
        json.dump(st, f, ensure_ascii=False)
    out = git_sync("Antwort " + aid + " " + art, ["status/" + aid + ".json"])
    return f"Antwort an Grok gespeichert: {art.upper()} ({aid})" + ("" if out else " - Push unklar, laeuft beim naechsten Lauf mit")


def main():
    push = "--kein-push" not in sys.argv
    git_sync("", [], push=False)  # nur pull: neue Grok-Auftraege holen
    neu, offen_n, geaendert = briefkasten(senden=push)
    jetzt = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    n_ok, tot = dienste()
    akku, htemp = honor()
    xok, xtemp, n8n = xiaomi()
    fn, facts = fails24()
    t = [f"# JACK Lage {jetzt} (Bremen)", "",
         "Kurzfassung fuer Tesla: lies die Punkte vor, hoechstens zwei Saetze pro Punkt.", "",
         f"- JACK-Dienste: {n_ok} von {len(KERN)} laufen" + (f", AUS: {', '.join(tot)}" if tot else ", alles gruen"),
         f"- Honor: Akku {akku if akku is not None else '?'} %, {htemp if htemp is not None else '?'} Grad",
         f"- Xiaomi: {'erreichbar' if xok else 'NICHT erreichbar'}, {xtemp if xtemp is not None else '?'} Grad, n8n {n8n}",
         f"- Fehlgeschlagene JACK-Auftraege letzte 24 h: {fn}" + (f" ({facts})" if facts else ""),
         f"- Playlist-Rettung Musik gut: {playlist()} Songs",
         f"- Grok-Briefkasten: {offen_n} Fragen warten auf Dima" + (f", {neu} neu gemeldet" if neu else ""),
         "", "## Offene Entscheidungen und Fristen fuer Dima", offen(), "",
         "_Automatisch von JACK (Honor). Wahrheit ist das Honor, diese Datei ist nur ein Spiegel._", ""]
    os.makedirs(G + "/lage", exist_ok=True)
    open(G + "/lage/aktuell.md", "w").write("\n".join(t))
    print("\n".join(t[:10]))
    print("push:", git_sync("Lage " + jetzt, ["lage/aktuell.md"] + geaendert, push=push))


if __name__ == "__main__":
    main()
