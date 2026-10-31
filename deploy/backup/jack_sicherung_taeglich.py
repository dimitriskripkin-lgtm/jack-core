#!/usr/bin/env python3
"""Z3b Cron-Einstieg; nur explizites --run; Implementierung separat importieren."""
import os, sys

if __name__=='__main__':
    if sys.argv[1:]!=['--run']:
        raise SystemExit('Nur nach Claude/Dima-Review mit --run starten')
    os.umask(0o077)
    sys.path.insert(0, '/data/data/com.termux/files/home/jack')  # Claude 31.10.: jack_xiaomi im Cron auffindbar
    import jack_sicherung_taeglich_impl as impl
    impl.run()
