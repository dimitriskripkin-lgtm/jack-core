"""JACK_TUNE_DIALOG: Dialogkanal fuer Claude. Spricht ueber handle() wie Dima, aber ohne Telegram.
Aufruf: python3 jack_dialog.py <base64-Text> [neu]   -> Antwort auf stdout
Eigenes Fenster reports/dialog_window.jsonl, Dimas talk_window bleibt unberuehrt.
Log: reports/dialog_log.jsonl. Nur lokal, kein Netz-Eingang."""
import sys, os, json, time, base64
H = os.path.expanduser("~/jack")
sys.path.insert(0, H)
WIN = H + "/reports/dialog_window.jsonl"
LOG = H + "/reports/dialog_log.jsonl"

def _load():
    try:
        return [tuple(json.loads(l)) for l in open(WIN, encoding="utf-8").read().splitlines()[-8:]]
    except Exception:
        return []

def frage(text, neu=False):
    import jack_telegram as T
    import jack_talk as JT
    win = [] if neu else _load()
    JT._ROLLING_WINDOW = win if win else [("(Start)", "ok")]
    out = []
    keep = {}
    for n in ("send", "send_keyboard"):
        if hasattr(T, n):
            keep[n] = getattr(T, n)
            setattr(T, n, lambda *a, **k: out.append(str(a[0]) if a else ""))
    try:
        r = T.handle(text)
    finally:
        for n, f in keep.items():
            setattr(T, n, f)
    teile = ([str(r)] if r else []) + out
    antwort = "\n---\n".join(teile) if teile else "(keine Antwort)"
    if not (text.lstrip().startswith("/")):
        win = [w for w in win if w[0] != "(Start)"]
        win.append((text[:240], antwort[:700]))
    win = win[-8:]
    open(WIN, "w", encoding="utf-8").write("\n".join(json.dumps(list(w), ensure_ascii=False) for w in win) + "\n")
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.strftime("%F %T"), "q": text, "a": antwort}, ensure_ascii=False) + "\n")
    return antwort

if __name__ == "__main__":
    t = base64.b64decode(sys.argv[1]).decode("utf-8")
    print(frage(t, len(sys.argv) > 2 and sys.argv[2] == "neu"))
