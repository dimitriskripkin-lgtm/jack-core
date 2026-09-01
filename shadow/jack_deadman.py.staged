#!/data/data/com.termux/files/usr/bin/python3
try:
    from jack_dm_gate import allow as _dm3h_allow  # JACK_TUNE_DM3H
except Exception:
    def _dm3h_allow(min_s=10800):
        return True
"""Dead-Man: wenn Overmind/Waechter zu lange still → Telegram-Hinweis."""
import os, time, subprocess
from pathlib import Path
H = Path("/data/data/com.termux/files/home/jack")
MAX_AGE_H = 3  # Stunden

def age(p):
    try:
        return (time.time() - Path(p).stat().st_mtime) / 3600.0
    except Exception:
        return 999.0

def notify(msg):
    try:
        subprocess.run(
            ["python3", "-c",
             f"import jack_telegram; jack_telegram.send({msg!r}) if _dm3h_allow() else None"],
            cwd=str(H), timeout=15, capture_output=True,
        )
    except Exception:
        pass

def main():
    checks = {
        "overmind_result": H / "jack_overmind_result.json",
        "waechter_hb": H / ".heartbeat_jack_waechter",
        "health": H / "jack_health_now.json",
    }
    stale = []
    for name, path in checks.items():
        a = age(path)
        if a > MAX_AGE_H:
            stale.append(f"{name}:{a:.1f}h")
    if stale:
        msg = "Hinweis: Überwachung meldet alte Dateien (> %sh): %s. Kein Absturz — nur frische Messung fehlt." % (MAX_AGE_H, ", ".join(stale))
        print(msg)
        notify(msg)
        return 1
    print("DEADMAN OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
