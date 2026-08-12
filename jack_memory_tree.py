#!/usr/bin/env python3
"""Baumstruktur fuer JACK Memory.
Jede Erinnerung kann einen Parent haben -> Kontext-Ketten sind abfragbar.
Beispiel: Bug -> Fix -> Test -> Deploy als verfolgbare Kette."""
import os, sqlite3, datetime
try:
    import jack_logging as _jlog
except Exception:
    _jlog = None
sys_path = os.path.expanduser('~/jack')
DB = os.path.expanduser('~/jack/jack_memory.db')
SESSION_FILE = os.path.expanduser('~/jack/.aktuelle_session_id')

def get_session_parent():
    """Gibt die letzte Memory-ID der aktuellen Session zurueck."""
    try:
        return open(SESSION_FILE).read().strip() or None
    except Exception:
        return None

def set_session_parent(memory_id):
    """Setzt die aktuelle Session-ID."""
    try:
        open(SESSION_FILE, 'w').write(str(memory_id))
    except Exception as _le:
        _jlog and _jlog.fehler("jack_memory_tree","unbenannt",_le)

def reset_session():
    """Neue Session starten - kein Parent."""
    try:
        os.remove(SESSION_FILE)
    except Exception as _le:
        _jlog and _jlog.fehler("jack_memory_tree","unbenannt",_le)

def save_with_parent(cmd, result, kontext_typ='chat', parent_id=None, auto_chain=True):
    """Speichert Erinnerung mit optionalem Parent.
    auto_chain=True: letzter Eintrag dieser Session wird automatisch Parent."""
    import secrets, hashlib
    hex_id = secrets.token_hex(8)
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if parent_id is None and auto_chain:
        parent_id = get_session_parent()

    try:
        import jack_db_queue as _dq
        ok, rowid = _dq.write(DB,
            'INSERT INTO memory(id,cmd,result,intent,time,timestamp,source,parent_id,kontext_typ) VALUES(?,?,?,?,?,?,?,?,?)',
            (hex_id, cmd, result, 'unknown', ts, ts, kontext_typ, parent_id, kontext_typ),
            wait=True)
        if not ok:
            return None, None
        if auto_chain:
            set_session_parent(hex_id)
        return hex_id, rowid
    except Exception as e:
        return None, None

def kette_rueckwaerts(memory_id, limit=10):
    """Findet den Pfad von einer Erinnerung bis zur Wurzel."""
    try:
        con = sqlite3.connect(DB)
        rows = con.execute('''
            WITH RECURSIVE wurzel(id, cmd, result, ts, typ, parent_id, tiefe) AS (
                SELECT id, cmd, result, timestamp, kontext_typ, parent_id, 0
                FROM memory WHERE id = ?
                UNION ALL
                SELECT m.id, m.cmd, m.result, m.timestamp, m.kontext_typ, m.parent_id, w.tiefe - 1
                FROM memory m JOIN wurzel w ON m.id = w.parent_id
                LIMIT ?
            )
            SELECT id, cmd, result, ts, typ, tiefe FROM wurzel ORDER BY tiefe
        ''', (memory_id, limit)).fetchall()
        con.close()
        return rows
    except Exception as e:
        return []

def kette_vorwaerts(memory_id, limit=20):
    """Findet alle Nachfolger einer Erinnerung (Unterbaum)."""
    try:
        con = sqlite3.connect(DB)
        rows = con.execute('''
            WITH RECURSIVE baum(id, cmd, result, ts, typ, parent_id, tiefe) AS (
                SELECT id, cmd, result, timestamp, kontext_typ, parent_id, 0
                FROM memory WHERE id = ?
                UNION ALL
                SELECT m.id, m.cmd, m.result, m.timestamp, m.kontext_typ, m.parent_id, b.tiefe + 1
                FROM memory m JOIN baum b ON m.parent_id = b.id
                LIMIT ?
            )
            SELECT id, cmd, result, ts, typ, tiefe FROM baum ORDER BY tiefe, ts
        ''', (memory_id, limit)).fetchall()
        con.close()
        return rows
    except Exception as e:
        return []

def geschwister(parent_id):
    """Alle Erinnerungen mit demselben Parent."""
    try:
        con = sqlite3.connect(DB)
        rows = con.execute(
            'SELECT id, cmd, result, timestamp, kontext_typ FROM memory WHERE parent_id = ? ORDER BY timestamp',
            (parent_id,)
        ).fetchall()
        con.close()
        return rows
    except Exception:
        return []

def baum_text(memory_id, richtung='beide'):
    """Gibt den Kontext-Baum als lesbaren Text zurueck."""
    zeilen = []
    if richtung in ('rueckwaerts', 'beide'):
        chain = kette_rueckwaerts(memory_id)
        if chain:
            zeilen.append('Kontext-Kette (rueckwaerts):')
            for row in chain:
                tid, cmd, result, ts, typ, tiefe = row
                prefix = '  ' * abs(tiefe) + ('-> ' if tiefe == 0 else '<- ')
                zeilen.append(prefix + '[' + typ + '] ' + cmd[:60] + ' (' + ts[:16] + ')')
    if richtung in ('vorwaerts', 'beide'):
        sub = kette_vorwaerts(memory_id)
        if len(sub) > 1:
            zeilen.append('')
            zeilen.append('Nachfolger:')
            for row in sub[1:]:
                tid, cmd, result, ts, typ, tiefe = row
                prefix = '  ' * tiefe + '-> '
                zeilen.append(prefix + '[' + typ + '] ' + cmd[:60])
    return chr(10).join(zeilen) if zeilen else 'Keine Verbindungen gefunden'

def letzte_kette(limit=5):
    """Letzte zusammenhaengende Kette der aktuellen Session."""
    pid = get_session_parent()
    if not pid:
        return 'Keine aktive Session'
    return baum_text(pid, 'rueckwaerts')

def statistik():
    """Wie viele Erinnerungen haben Parents?"""
    try:
        con = sqlite3.connect(DB)
        total = con.execute('SELECT COUNT(*) FROM memory').fetchone()[0]
        mit_parent = con.execute('SELECT COUNT(*) FROM memory WHERE parent_id IS NOT NULL').fetchone()[0]
        wurzeln = total - mit_parent
        tiefste = con.execute('''
            WITH RECURSIVE t(id, tiefe) AS (
                SELECT id, 0 FROM memory WHERE parent_id IS NULL
                UNION ALL
                SELECT m.id, t.tiefe+1 FROM memory m JOIN t ON m.parent_id = t.id
            )
            SELECT MAX(tiefe) FROM t
        ''').fetchone()[0] or 0
        con.close()
        return (
            'Memory-Baum Statistik:' + chr(10) +
            'Gesamt: ' + str(total) + chr(10) +
            'Mit Parent (vernetzt): ' + str(mit_parent) + chr(10) +
            'Wurzeln (Kettenanfaenge): ' + str(wurzeln) + chr(10) +
            'Tiefste Kette: ' + str(tiefste) + ' Schritte'
        )
    except Exception as e:
        return 'Fehler: ' + str(e)[:100]

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == 'stat':
            print(statistik())
        elif sys.argv[1] == 'kette' and len(sys.argv) > 2:
            print(baum_text(sys.argv[2]))
        elif sys.argv[1] == 'session':
            print(letzte_kette())
        elif sys.argv[1] == 'reset':
            reset_session()
            print('Session zurueckgesetzt')
    else:
        print(statistik())
