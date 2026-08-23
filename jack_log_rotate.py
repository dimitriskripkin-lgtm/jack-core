#!/usr/bin/env python3
"""Log-Rotation: alle .log-Dateien ueber 5MB kuerzen."""
import os, glob

H = os.path.expanduser("~/jack")
MAX_BYTES = 5 * 1024 * 1024  # 5MB
KEEP_LINES = 1000

def rotate_all():
    rotated = []
    for f in glob.glob(os.path.join(H, "*.log")):
        if os.path.getsize(f) > MAX_BYTES:
            try:
                lines = open(f, encoding="utf-8", errors="ignore").readlines()
                open(f, "w").write("".join(lines[-KEEP_LINES:]))
                rotated.append(os.path.basename(f))
            except Exception as e:
                print(f"Rotation fehlgeschlagen {f}: {e}")
    return rotated

if __name__ == "__main__":
    r = rotate_all()
    print(f"Rotiert: {r}" if r else "Alle Logs unter 5MB - nichts zu tun")
