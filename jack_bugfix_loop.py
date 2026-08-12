#!/usr/bin/env python3
"""Autonomer Bugfix: Bug aus errors.db -> Analyse -> Fix -> Test -> Freigabe."""
import os, sys, sqlite3, subprocess, datetime, shutil
sys.path.insert(0, os.path.expanduser('~/jack'))

DB = os.path.expanduser('~/jack/jack_errors.db')
H = os.path.expanduser('~/jack')

def hole_kandidaten(limit=3):
    """Holt unfixte Bugs aus errors.db die in JACK-Dateien liegen."""
    try:
        con = sqlite3.connect(DB)
        rows = con.execute("""
            SELECT id, module, error_type, error_msg, file_path, line_num, context, timestamp
            FROM errors
            WHERE resolved=0
            AND file_path LIKE '%/jack/%'
            AND file_path NOT LIKE '%test%'
            ORDER BY id DESC LIMIT ?
        """, (limit,)).fetchall()
        con.close()
        return [{'id':r[0],'module':r[1],'type':r[2],'msg':r[3],
                 'file':r[4],'line':r[5],'hint':r[6],'ts':r[7]} for r in rows]
    except Exception as e:
        return []

def analysiere(bug):
    """Traceback-Parser + Gemini fuer Loesungsvorschlag."""
    import jack_traceback as _jt
    tb_text = f"File \"{bug['file']}\", line {bug['line']}\n{bug['type']}: {bug['msg']}"
    parsed = _jt.parse(tb_text)
    return parsed

def generiere_fix(bug, analyse):
    """Gemini generiert einen konkreten Fix."""
    import jack_gemini_bridge as _gb
    if not bug.get('file') or not os.path.exists(bug['file']):
        return None, 'Datei nicht gefunden: ' + str(bug.get('file'))

    code = open(bug['file']).read()
    # Kontext: Zeilen um den Fehler
    lines = code.split('\n')
    start = max(0, bug['line']-5)
    end = min(len(lines), bug['line']+5)
    kontext = '\n'.join([f"{i+1}: {l}" for i,l in enumerate(lines[start:end], start=start)])

    prompt = (
        f"Python Bug in {os.path.basename(bug['file'])} Zeile {bug['line']}:\n"
        f"Fehler: {bug['type']}: {bug['msg']}\n"
        f"Hinweis: {analyse.get('loesungshinweis','')}\n\n"
        f"Code-Kontext:\n{kontext}\n\n"
        f"Erstelle einen minimalen Fix als SEARCH/REPLACE Block:\n"
        f"<<<SEARCH\n<alter code>\n===\n<neuer code>\n>>>REPLACE\n\n"
        f"Nur den Fix, keine Erklaerung."
    )
    try:
        antwort = _gb.ask_gemini(prompt)
        return antwort, None
    except Exception as e:
        return None, str(e)[:200]

def wende_fix_an(datei, fix_text):
    """Wendet SEARCH/REPLACE Fix an."""
    if '<<<SEARCH' not in fix_text or '>>>REPLACE' not in fix_text:
        return False, 'Kein valides SEARCH/REPLACE Format'

    try:
        teil = fix_text.split('<<<SEARCH')[1].split('>>>REPLACE')
        search_replace = teil[0].split('===')
        if len(search_replace) != 2:
            return False, 'Format-Fehler: kein === Trenner'

        search = search_replace[0].strip()
        replace = search_replace[1].strip()
        code = open(datei).read()

        if search not in code:
            return False, f'SEARCH nicht gefunden in {os.path.basename(datei)}'

        shutil.copy(datei, datei + '.bugfix_bak')
        new_code = code.replace(search, replace, 1)
        open(datei, 'w').write(new_code)
        return True, f'{len(search)} Zeichen ersetzt'
    except Exception as e:
        return False, str(e)[:200]

def teste_fix(datei):
    """py_compile + Selftest als Regression-Check."""
    r = subprocess.run(['python3','-m','py_compile',datei], capture_output=True)
    if r.returncode != 0:
        return False, 'Syntax-Fehler: ' + r.stderr.decode()[:200]
    # Selftest
    r2 = subprocess.run(['python3', os.path.join(H,'jack_selftest.py')],
        capture_output=True, text=True, timeout=30)
    import re
    clean = re.sub(r'\x1b\[[0-9;]*m','',r2.stdout)
    if '5/5' in clean:
        return True, 'Selftest 5/5 OK'
    elif '4/5' in clean:
        return True, 'Selftest 4/5 - Temp evtl. erhoeht'
    else:
        return False, 'Selftest verschlechtert: ' + clean[-100:]

def rollback(datei):
    bak = datei + '.bugfix_bak'
    if os.path.exists(bak):
        shutil.copy(bak, datei)
        os.remove(bak)
        return True
    return False

def markiere_resolved(bug_id, fix_text):
    try:
        con = sqlite3.connect(DB)
        con.execute("UPDATE errors SET resolved=1, context=? WHERE id=?",
            (fix_text[:200], bug_id))
        con.commit(); con.close()
        return True
    except: return False

def run(max_bugs=1):
    """Hauptloop: ein Bug pro Durchlauf fuer Sicherheit."""
    import jack_telegram as _jt_tg
    kandidaten = hole_kandidaten(max_bugs)
    if not kandidaten:
        return 'Keine fixbaren Bugs in errors.db gefunden.'

    ergebnisse = []
    for bug in kandidaten:
        msg = [f"Bug #{bug['id']}: {bug['type']} in {os.path.basename(bug['file'])} Z{bug['line']}"]
        msg.append(f"Fehler: {bug['msg'][:100]}")

        # 1. Analyse
        analyse = analysiere(bug)
        msg.append(f"Hinweis: {analyse.get('loesungshinweis','?')}")

        # 2. Fix generieren
        fix_text, err = generiere_fix(bug, analyse)
        if err or not fix_text:
            msg.append(f"Fix-Generierung fehlgeschlagen: {err}")
            ergebnisse.append(chr(10).join(msg))
            continue

        # 3. Fix anwenden
        ok, detail = wende_fix_an(bug['file'], fix_text)
        if not ok:
            msg.append(f"Fix konnte nicht angewendet werden: {detail}")
            ergebnisse.append(chr(10).join(msg))
            continue
        msg.append(f"Fix angewendet: {detail}")

        # 4. Testen
        test_ok, test_detail = teste_fix(bug['file'])
        if not test_ok:
            rollback(bug['file'])
            msg.append(f"Test fehlgeschlagen - Rollback: {test_detail}")
            ergebnisse.append(chr(10).join(msg))
            continue
        msg.append(f"Test OK: {test_detail}")

        # 5. Freigabe anfragen
        freigabe_text = (
            chr(10).join(msg) + chr(10) + chr(10) +
            "Soll ich diesen Fix deployen und als geloest markieren?"
        )
        _jt_tg.send_keyboard(
            freigabe_text[:3000],
            [[("✅ Deployen", f"bugfix_deploy:{bug['id']}"),
              ("❌ Rollback", f"bugfix_rollback:{bug['id']}")]]
        )
        ergebnisse.append('Freigabe angefragt fuer Bug #' + str(bug['id']))

    return chr(10).join(ergebnisse) if ergebnisse else 'Fertig'

if __name__ == '__main__':
    print(run())
