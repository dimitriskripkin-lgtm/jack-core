#!/usr/bin/env python3
import sqlite3, os
c = sqlite3.connect(os.path.expanduser("~/jack/jack_errors.db"))
rows = c.execute("SELECT module, error_msg FROM errors WHERE resolved=0 ORDER BY timestamp DESC LIMIT 5").fetchall()
c.close()
if not rows:
    print("Keine offenen Fehler")
else:
    for r in rows:
        print(r[0] + ": " + r[1][:80])
