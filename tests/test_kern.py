import sys, os
sys.path.insert(0, os.path.expanduser('~/jack'))

def test_memory_save_und_query():
    import jack_memory
    ok = jack_memory.save('pytest_test_cmd', 'pytest_test_result', 'test')
    assert ok, 'save() hat False zurueckgegeben'
    rows = jack_memory.query('pytest_test_cmd', n=5)
    assert any('pytest_test_cmd' in r[0] for r in rows), 'nicht gefunden'

def test_memory_kein_duplikat():
    import jack_memory, sqlite3
    jack_memory.save('duplikat_test_xy', 'wert', 'test')
    jack_memory.save('duplikat_test_xy', 'wert', 'test')
    con = sqlite3.connect(os.path.expanduser('~/jack/jack_memory.db'))
    n = con.execute("SELECT COUNT(*) FROM memory WHERE cmd='duplikat_test_xy'").fetchone()[0]
    con.close()
    assert n <= 2, f'Zu viele Eintraege: {n}'

def test_intent_erkennung():
    import jack_intent
    r = jack_intent.detect('der xiaomi nervt mich schon wieder')
    assert r is not None, 'Intent nicht erkannt'
    assert r['intent'] == 'ssh_check', f'Falscher Intent: {r["intent"]}'
    assert r['confidence'] >= 0.5, f'Confidence zu niedrig: {r["confidence"]}'

def test_selftest_laeuft():
    import subprocess, re
    r = subprocess.run(['python3', os.path.expanduser('~/jack/jack_selftest.py')],
        capture_output=True, text=True, timeout=30)
    clean = re.sub(r'\x1b\[[0-9;]*m', '', r.stdout)
    assert '5/5' in clean, f'Selftest nicht 5/5: {clean[-200:]}'

def test_chain_vollcheck():
    import jack_chains
    r = jack_chains.run('system_vollcheck')
    assert r['ok'], f'Chain fehlgeschlagen: {r["text"][:100]}'
    assert r['schritte'] >= 3, f'Zu wenige Schritte: {r["schritte"]}'

if __name__ == '__main__':
    tests = [test_memory_save_und_query, test_memory_kein_duplikat,
             test_intent_erkennung, test_selftest_laeuft, test_chain_vollcheck]
    ok = 0
    for t in tests:
        try:
            t(); print(f'[OK] {t.__name__}'); ok += 1
        except Exception as e:
            print(f'[ER] {t.__name__}: {e}')
    print(f'\n{ok}/{len(tests)} Tests bestanden')
