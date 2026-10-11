#!/data/data/com.termux/files/usr/bin/python3
"""Dead-Man (neu 10.10.2026): Telegram-Hinweis, wenn Waechter-Heartbeat oder Health-Datei zu alt sind.
Max. 1 Meldung pro MAX_AGE_H Stunden. Cron: cron/deadman.sh alle 30 Min."""
import time
from pathlib import Path

H = Path("/data/data/com.termux/files/home/jack")
MAX_AGE_H = 3
MARK = H / ".deadman_last"
CHECKS = {
    "waechter_hb": H / ".heartbeat_jack_waechter",
    "health": H / "jack_health_now.json",
}


def age(p):
    try:
        return (time.time() - Path(p).stat().st_mtime) / 3600.0
    except Exception:
        return 999.0


def main():
    stale = ["%s:%.1fh" % (n, age(p)) for n, p in CHECKS.items() if age(p) > MAX_AGE_H]
    if not stale:
        print("DEADMAN OK")
        return 0
    msg = "Dead-Man: Ueberwachung still (> %sh): %s" % (MAX_AGE_H, ", ".join(stale))
    print(msg)
    if age(MARK) < MAX_AGE_H:
        return 1
    try:
        import jack_telegram
        jack_telegram.send(msg)
        MARK.write_text(str(int(time.time())))
    except Exception as e:
        print("notify fehlgeschlagen:", type(e).__name__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
