import sys, time, json, os, sqlite3, subprocess
sys.path.insert(0, '/data/data/com.termux/files/home/jack')
from jack_android import _sh, get_ui_tree, adb_setup

CMD_FILE = '/sdcard/jack_cmd.json'
RESULT_FILE = '/sdcard/jack_result.json'
LOG_FILE = '/data/data/com.termux/files/home/jack/alpha.log'
SKILLS_DB = '/data/data/com.termux/files/home/jack/alpha_skills.db'
SKILLS_DIR = '/data/data/com.termux/files/home/jack/skills'

def log(msg):
    line = '[' + time.strftime('%H:%M:%S') + '] ' + str(msg)
    print(line, flush=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def init_db():
    c = sqlite3.connect(SKILLS_DB)
    c.execute('''CREATE TABLE IF NOT EXISTS skills (
        keyword TEXT, package TEXT, element_text TEXT,
        cx INT, cy INT, success_count INT DEFAULT 1,
        last_used TEXT, PRIMARY KEY(keyword, element_text))''')
    c.commit(); c.close()

def save_skill(keyword, package, element_text, center):
    c = sqlite3.connect(SKILLS_DB)
    c.execute('''INSERT INTO skills(keyword,package,element_text,cx,cy,last_used)
        VALUES(?,?,?,?,?,datetime('now'))
        ON CONFLICT(keyword,element_text) DO UPDATE SET
        success_count=success_count+1, last_used=datetime('now')''',
        (keyword, package, element_text, center[0], center[1]))
    c.commit()
    count = c.execute('SELECT success_count FROM skills WHERE keyword=? AND element_text=?',
        (keyword, element_text)).fetchone()
    c.close()
    cnt = count[0] if count else 1
    log('Skill gelernt: ' + keyword + ' -> ' + element_text + ' (' + str(cnt) + 'x)')
    if cnt >= 3:
        write_skill_file(keyword, package, element_text, center[0], center[1])
    return cnt

def lookup_skill(keyword):
    try:
        c = sqlite3.connect(SKILLS_DB)
        row = c.execute('''SELECT package, element_text, cx, cy, success_count
            FROM skills WHERE keyword=? ORDER BY success_count DESC LIMIT 1''',
            (keyword.lower(),)).fetchone()
        c.close()
        return row
    except Exception:
        return None

def write_skill_file(keyword, package, element_text, cx, cy):
    os.makedirs(SKILLS_DIR, exist_ok=True)
    path = SKILLS_DIR + '/skill_' + keyword + '.py'
    lines = [
        'import sys, time, subprocess',
        'sys.path.insert(0, "/data/data/com.termux/files/home/jack")',
        'from jack_android import _sh, adb_setup',
        'def run():',
        '    adb_setup()',
        '    _sh("am start -n ' + package + '", root=True)',
        '    time.sleep(2.5)',
        '    subprocess.run("adb -s 127.0.0.1:5555 shell input tap ' + str(cx) + ' ' + str(cy) + '", shell=True)',
        '    return {"ok": True, "skill": "' + keyword + '"}',
        'if __name__ == "__main__": print(run())'
    ]
    open(path, 'w').write('
'.join(lines))
    log('Skill-Datei geschrieben: ' + path)

def load_skill_file(keyword):
    path = SKILLS_DIR + '/skill_' + keyword + '.py'
    if os.path.exists(path):
        return path
    return None

def adb_tap(x, y):
    r = subprocess.run('adb -s 127.0.0.1:5555 shell input tap ' + str(x) + ' ' + str(y),
        shell=True, capture_output=True, text=True)
    log('adb tap ' + str(x) + ',' + str(y) + ' rc=' + str(r.returncode))
    return r.returncode == 0

def execute(cmd):
    goal = cmd.get('goal', '')
    package = cmd.get('package', '')
    keyword = goal.lower().split()[0]
    log('Auftrag: ' + goal)

    # Stufe 1: Skill-Datei vorhanden?
    skill_path = load_skill_file(keyword)
    if skill_path:
        log('Skill-Datei gefunden: ' + skill_path)
        r = subprocess.run(['python3', skill_path], capture_output=True, text=True, timeout=15)
        try:
            result = json.loads(r.stdout.strip())
            log('Skill ausgefuehrt: ' + str(result))
            return result
        except Exception:
            log('Skill-Fehler: ' + r.stderr[:100])

    # Stufe 2: DB-Skill bekannt?
    db_skill = lookup_skill(keyword)
    if db_skill and db_skill[4] >= 2:
        pkg, el_text, cx, cy, cnt = db_skill
        log('DB-Skill (' + str(cnt) + 'x): ' + el_text + ' -> tippe ' + str(cx) + ',' + str(cy))
        if pkg:
            _sh('am start -n ' + pkg, root=True)
            time.sleep(2.5)
        ok = adb_tap(cx, cy)
        save_skill(keyword, pkg or package, el_text, (cx, cy))
        return {'ok': ok, 'skill_db': True, 'element': el_text}

    # Stufe 3: XML-Scan
    if package:
        subprocess.run('adb -s 127.0.0.1:5555 shell input keyevent 3', shell=True)
        time.sleep(1)
        _sh('am start -n ' + package, root=True)
        time.sleep(3)
    els = get_ui_tree()
    log('UI: ' + str(len(els)) + ' Elemente')
    words = [w.lower() for w in goal.split() if len(w) > 2]
    for e in els:
        txt = e.get('text', '')
        dsc = e.get('desc', '')
        ctr = e.get('center', (0, 0))
        haystack = (txt + ' ' + dsc).lower()
        if any(w in haystack for w in words):
            log('XML-Treffer: ' + txt + ' -> tippe ' + str(ctr))
            ok = adb_tap(ctr[0], ctr[1])
            if ok:
                save_skill(keyword, package, txt, ctr)
            time.sleep(2)
            els2 = get_ui_tree()
            first = els2[0].get('text', '') if els2 else ''
            return {'ok': ok, 'aktion': 'tap', 'element': txt, 'danach': first}

    log('Kein Treffer')
    return {'ok': False, 'grund': 'Nicht gefunden', 'elemente': len(els)}

def main():
    log('JACK Node Alpha + Lern-System gestartet')
    init_db()
    adb_setup()
    log('Bereit')
    while True:
        try:
            if os.path.exists(CMD_FILE):
                with open(CMD_FILE) as f:
                    cmd = json.load(f)
                os.remove(CMD_FILE)
                log('CMD: ' + str(cmd))
                result = execute(cmd)
                with open(RESULT_FILE, 'w') as f:
                    json.dump(result, f)
                log('Result: ' + str(result))
        except Exception as e:
            log('FEHLER: ' + str(e))
        time.sleep(2)

main()
