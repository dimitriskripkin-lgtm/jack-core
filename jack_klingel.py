#!/usr/bin/env python3
"""JACK_TUNE_KLINGEL (26.10.2026, Kap 305): meldet per Telegram neue Post im Briefkasten,
in beide Richtungen: ChatGPT -> Claude und Claude -> ChatGPT (JACK_TUNE_KLINGEL2).
Cron alle 5 Min. Aus: ~/jack/.klingel_off. Nur lesen + je Richtung 1 Meldung."""
import json, os, re, sys
J = "/data/data/com.termux/files/home/jack"
B = J + "/ARBEITSPLATZ/BUEROS/"
DRY = os.environ.get("KLINGEL_DRY") == "1"
# (Datei, Statusdatei, Absender im Kopf, Kopf ist Titel?, Text, Hinweis)
WEGE = [
    (os.environ.get("KLINGEL_FILE", B + "claude/eingang.md"),
     os.environ.get("KLINGEL_STATE", J + "/logs/.klingel_state.json"),
     r"chatgpt", False, "Post von ChatGPT im Claude-Briefkasten:", "Sag Claude: Schau in den Briefkasten."),
    (os.environ.get("KLINGEL_FILE2", B + "chatgpt/eingang.md"),
     os.environ.get("KLINGEL_STATE2", J + "/logs/.klingel_state_chatgpt.json"),
     r"claude", True, "Post von Claude im ChatGPT-Briefkasten:", "Sag ChatGPT: Schau in deinen Briefkasten."),
]

def titel_aus(txt, wer, kopf_ist_titel):
    titel = []
    zeilen = txt.splitlines()
    for i, z in enumerate(zeilen):
        if re.match(r"^#{2,3} .*" + wer, z, re.I):
            if kopf_ist_titel:
                t = re.sub(r"^#+\s*", "", z)
                t = re.sub(r"^\d{4}-\d\d-\d\d\s+[\d:]+\s*", "", t).strip()
                if t and t.lower() != wer:  # Auto-Kopf "<zeit> claude" vom Briefkasten ueberspringen
                    titel.append(t[:90])
                continue
            for w in zeilen[i + 1:i + 4]:
                w = w.strip().lstrip("#").strip()
                if w:
                    titel.append(w[:90]); break
    return titel

def ein_weg(ein, st, wer, kopf_ist_titel, kopf, hinweis):
    try:
        s = os.stat(ein)
    except OSError:
        return 0
    try:
        alt = json.load(open(st))
    except (OSError, ValueError):
        alt = None
    neu = {"ino": s.st_ino, "size": s.st_size}
    if not alt or alt.get("ino") != s.st_ino or s.st_size < alt.get("size", 0):
        json.dump(neu, open(st, "w"))  # erster Lauf oder rotiert: nur merken, nicht klingeln
        return 0
    if s.st_size == alt["size"]:
        return 0
    with open(ein, "rb") as f:
        f.seek(alt["size"])
        txt = f.read(65536).decode("utf-8", "replace")
    titel = titel_aus(txt, wer, kopf_ist_titel)
    if titel:
        text = kopf + "\n- " + "\n- ".join(titel[:3]) + "\n" + hinweis
        if DRY:
            print(text); r = {"status": "GESENDET"}
        else:
            sys.path.insert(0, J)
            import jack_tg_send
            r = jack_tg_send.send(text, wichtig=True, quelle="klingel")
        if r.get("status") not in ("GESENDET", "GEPUFFERT", "NUR_LOG"):
            return 1  # Stand nicht weiterschieben, naechster Lauf versucht erneut
    json.dump(neu, open(st, "w"))
    return 0

def main():
    if os.path.exists(J + "/.klingel_off"):
        return 0
    rc = 0
    for w in WEGE:
        try:
            rc |= ein_weg(*w)
        except Exception:
            rc |= 1
    return rc

if __name__ == "__main__":
    sys.exit(main())
