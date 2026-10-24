#!/usr/bin/env python3
"""JACK_TUNE_SELBSTBILD (A20a): kompaktes, belegbares Selbstbild (Kap. 292/294).

Schreibt atomar JACK_HOME/reports/selbstbild.md (max. 1500 Zeichen).
Nur lokale Lesequellen, mit einer dokumentierten Ausnahme: jack_lagebild.lagebild()
aktualisiert bei der Fahrmodusmessung seinen bestehenden Cache .fahrmodus.
Kein Telegram, kein Gemini/Groq, keine Missionen. Live-Einbau nur nach Claude/Dima-Go.
"""

import datetime as dt
import os
import pathlib
import re
import subprocess
import tempfile

JACK_HOME = pathlib.Path(os.environ.get('JACK_HOME', '/data/data/com.termux/files/home/jack'))
MAX_CHARS = 850  # CLAUDE_A20A_REVIEW: ask_groq kappt System-Prompt bei 4000, Basis ca. 2600


def _clean(value, limit=80):
    """Keine Steuerzeichen, Zeilenumbrueche oder versehentliche Token im Modellkontext."""
    s = ' '.join(str(value).split())
    s = re.sub(r'(?i)Bearer\s+\S+|gh[pousr]_[A-Za-z0-9_]{12,}|sk-[A-Za-z0-9_-]{15,}|AIza[A-Za-z0-9_-]{20,}', '[GESCHUETZT]', s)
    return s[:limit]


def _akku_wert(value):
    """Nur verifizierbare Prozentzahlen aus jack_lagebild, niemals raten/aufrunden."""
    if type(value) is not int or not 0 <= value <= 100:
        return 'unbekannt'
    return f'{value} % (Messwert)'


def _val(value, unit=''):
    return ('unbekannt' if value is None else _clean(value, 24) + unit)


def _lade_lagebild():
    try:
        import jack_lagebild  # reales Modul auf HONOR, Stand Kap. 292
        data = jack_lagebild.lagebild()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _handbuch(root):
    p = root / 'BETRIEBSHANDBUCH'
    try:
        files = [(int(m.group(1)), f) for f in p.iterdir()
                 if f.is_file() and (m := re.match(r'^(\d+)_.*\.md$', f.name))]
    except OSError:
        return ['unbekannt']
    rows = []
    for nr, f in sorted(files, key=lambda x: x[0], reverse=True)[:5]:
        title = f.stem
        first = 'unbekannt (keine Inhaltszeile)'
        try:
            with f.open(encoding='utf-8', errors='replace') as fh:
                title_found = False
                for raw in fh:
                    line = raw.strip()
                    if not line:
                        continue
                    if line.startswith('#'):
                        if not title_found:
                            title = line.lstrip('#').strip() or f.stem
                            title_found = True
                        continue
                    if line.startswith(('---', '```')):
                        continue
                    first = line
                    break
        except OSError:
            first = 'unbekannt (Datei nicht lesbar)'
        nrstr = str(nr) + ' '
        t = _clean(re.sub(r'^\d+\s+', '', title), 39)
        available = 120 - len(nrstr) - len(t) - 3
        rows.append(nrstr + t + ' | ' + _clean(first, max(1, available)))
    return rows or ['unbekannt']


def _git(root):
    try:
        r = subprocess.run(['git', '-C', str(root), 'log', '--oneline', '-5'],
                           capture_output=True, text=True, timeout=1.5,
                           stdin=subprocess.DEVNULL)
        if r.returncode:
            return ['unbekannt']
        return [_clean(s, 78) for s in r.stdout.splitlines()[:5]] or ['keine']
    except (OSError, subprocess.TimeoutExpired):
        return ['unbekannt']


def _bugkarte(root):
    p = root / 'ARBEITSPLATZ/gemeinsam/BUGKARTE_20261017.md'
    try:
        content = p.read_text(encoding='utf-8', errors='replace')[:30000]
    except OSError:
        return ['unbekannt']
    part = content.split('## Offen (priorisiert)', 1)
    if len(part) == 1:
        return ['unbekannt']
    section = part[1].split('\n## ', 1)[0]
    items = []
    for line in section.splitlines():
        if not re.match(r'^\d+\.\s', line):
            continue
        line = re.sub(r'^\d+\.\s*', '', line).replace('**', '').replace('\x60', '')
        title = re.split(r'[:;.]\s', line, maxsplit=1)[0]
        items.append(_clean(title, 78))
    return items[:3] or ['keine Eintraege']


def build(root=JACK_HOME, lage=None, stamp=None, handbuch_fn=None, git_fn=None, bug_fn=None):
    root = pathlib.Path(root)
    stamp = stamp or dt.datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %z')
    lage = _lade_lagebild() if lage is None else lage
    h, xi, fm = (lage.get(k) or {} for k in ('honor', 'xiaomi', 'fahrmodus'))
    bt = h.get('bluetooth') or {}
    xs = xi.get('status') or ('OK' if xi.get('ok') else 'UNBEKANNT')
    if fm.get('unsicher') or not fm.get('geprueft'):
        fahr = 'UNSICHER (keine frische Bestaetigung)'
    elif fm.get('aktiv') is True:
        fahr = 'LKW-Bluetooth erkannt: ' + _clean(fm.get('geraet') or 'Name fehlt', 28)
    elif fm.get('aktiv') is False:
        fahr = 'LKW-Bluetooth nicht erkannt (keine Aussage ueber Bewegung)'
    else:
        fahr = 'unbekannt'
    count = xi.get('benachrichtigungen')
    count = sum(n for n in count.values() if type(n) is int) if isinstance(count, dict) else None
    hb = handbuch_fn(root) if handbuch_fn else _handbuch(root)
    git = git_fn(root) if git_fn else _git(root)
    bugs = bug_fn(root) if bug_fn else _bugkarte(root)
    rows = [
        'JACK-SELBSTBILD | Erzeugt ' + _clean(stamp, 42),
        'Momentaufnahme, kein Beweis fuer alle Dienste oder den aktuellen GitHub-Stand.',
        f'HONOR: Akku {_akku_wert(h.get("akku"))}, Temp {_val(h.get("temp_c"), "C")}, BT ' +
        ('OK' if bt.get('ok') else 'UNBEKANNT') + ', Audiogeraet ' + _clean(bt.get('aktiv') or 'unbekannt', 32),
        f'XIAOMI: { _clean(xs, 18) }, Akku {_akku_wert(xi.get("akku"))}, Temp {_val(xi.get("temp_c"), "C")}, Benachrichtigungen {_val(count)} (nur Anzahl)',
        'Fahrmodus: ' + fahr,
        'Befehle: /standort GPS, /akku, /status, /lage, /timer, /musik, /agent, /scan, /selftest, /sensor, /budget, /vorschlaege, /links, /befehle (alle)',  # JACK_TUNE_HEUTEBEFEHLE (24.10.)
        'Handbuch (5 neueste Kapitel):',
    ]
    rows += ['- ' + _clean(s, 120) for s in hb[:5]]
    rows += ['Git lokal (5 letzte Commits, kein Push-Nachweis):']
    rows += ['- ' + _clean(s, 80) for s in git[:5]]
    rows += ['Bugkarte 17.10 (damals offen, heute NICHT neu verifiziert):']
    rows += ['- ' + _clean(s, 82) for s in bugs[:3]]
    text = '\n'.join(rows)
    if len(text) >= MAX_CHARS:
        text = text[:MAX_CHARS - 16].rsplit('\n', 1)[0] + '\n[GEKUERZT]'
    return text


def generate(root=JACK_HOME):
    root = pathlib.Path(root)
    content = build(root)
    dest_dir = root / 'reports'
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / 'selbstbild.md'
    temp = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=dest_dir,
                                         prefix='.selbstbild_', suffix='.tmp', delete=False) as fp:
            temp = pathlib.Path(fp.name)
            os.fchmod(fp.fileno(), 0o600)
            fp.write(content + '\n')
            fp.flush()
            os.fsync(fp.fileno())
        os.replace(temp, dest)
        return dest
    finally:
        if temp is not None and temp.exists():
            temp.unlink()


if __name__ == '__main__':
    print(generate())
