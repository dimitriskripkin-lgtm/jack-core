# SHA256: 14f45f59703fd727aa954eea006163d43f290a5119c0248ce3f05d0f3e58529b (SHA256 of source excluding this comment line, Claude-Fassung 24.10.)
"""JACK_TUNE_HEUTE: local, read-only account of JACK's evidenced activities."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import re

HOME = Path('/data/data/com.termux/files/home/jack')
CHECKS = {'grep_count', 'sv_ok', 'hb_ok', 'file_exists', 'diag', 'fact', 'compile_ok'}


def _norm(text):
    text = str(text or '').casefold()
    for a, b in [('ä', 'ae'), ('ö', 'oe'), ('ü', 'ue'), ('ß', 'ss')]:
        text = text.replace(a, b)
    return ' '.join(re.findall(r'[a-z0-9]+', text))


def _intent(text):
    """Return 'today', 'shift', or None; patterns deliberately narrow."""
    t = _norm(text)
    whole = ' ' + t + ' '
    # Require today's accomplishment question; not generic 'what did you ...'.
    if re.search(r'\b(was|welche|wieviel)\b.*\b(waehrend|in)\b.*\b(meiner|der|letzten)\b\s*\b(schicht|nacht)\b.*\b(gemacht|erledigt|getan|passiert)\b', t):
        return 'shift'
    if re.search(r'\b(was|welche|wieviel)\b.*\b(hast|hat)\b.*\b(du|jack)\b.*\b(heute)\b.*\b(gemacht|erledigt|getan)\b', t):
        # Filter questions about what JACK consumed/ate or other personal topics.
        return 'today'
    if re.search(r'\b(hast|habt)\s+(du|ihr)\b.*\bheute\b.*\b(was|etwas)\b.*\b(fuer mich)\b.*\b(getan|erledigt|gemacht)\b', t):
        return 'today'
    if re.search(r'\bwas\b.*\b(war|ist)\b.*\bheute\b.*\blos\b.*\b(bei dir|bei jack)\b', t):
        return 'today'
    return None


def erkennt(text):
    return not (HOME / '.heute_off').exists() and _intent(text) is not None


def _local_now(now):
    t = now if now is not None else datetime.now().astimezone()
    if t.tzinfo is not None:
        t = t.astimezone().replace(tzinfo=None)
    return t


def _clean_firstline(value):
    # No raw multiline chat/mission content; redact suspicious credentials.
    line = str(value or '').splitlines()[0] if value else ''
    line = re.sub(r'(?i)(bearer\s+\S+|gh[pousr]_[A-Za-z0-9_]{12,}|sk-[\w-]{15,})', '[geschuetzt]', line)
    line = re.sub(r'[\x00-\x1f\x7f]', ' ', line).strip()
    return (line[:67] + '...') if len(line) > 70 else line


def _src(value):
    value = str(value or 'unbekannt').lower()
    return value if re.fullmatch(r'[a-z0-9_-]{1,24}', value) else 'unbekannt'


def antwort(text, now=None, home='/data/data/com.termux/files/home/jack'):
    root = Path(home)
    if (root / '.heute_off').exists() or _intent(text) is None:
        return None
    current = _local_now(now)
    start = (current - timedelta(hours=12)) if _intent(text) == 'shift' else current.replace(hour=0, minute=0, second=0, microsecond=0)
    intro = 'Letzte 12 Stunden' if _intent(text) == 'shift' else 'Heute'
    notes = []
    answers = 0
    damage = 0
    log = root / 'logs' / 'telegram_chat.jsonl'
    try:
        with log.open('r', encoding='utf-8', errors='replace') as fh:
            for raw in fh:
                try:
                    row = json.loads(raw)
                    if not isinstance(row, dict):
                        raise ValueError('non-object')
                    ts = datetime.strptime(str(row['ts']), '%Y-%m-%d %H:%M:%S')
                    if not start <= ts <= current:
                        continue
                    if row.get('von') != 'jack':
                        continue
                    msg = _clean_firstline(row.get('text'))
                    if not msg or msg == 'JACK online.' or row.get('quelle') == 'claude_test':
                        continue
                    if not row.get('quelle') or row.get('quelle') == 'telegram':
                        answers += 1
                    else:
                        notes.append((ts, msg))
                except (ValueError, TypeError, KeyError, OverflowError):
                    damage += 1
    except FileNotFoundError:
        pass  # No fabricated history.
    except OSError:
        damage += 1

    sources = Counter()
    checks = Counter()
    fail = Counter()
    for directory, failed in (('done', False), ('fail', True)):
        path = root / 'missions' / directory
        try:
            with os.scandir(path) as it:
                for e in it:
                    try:
                        if not e.is_file(follow_symlinks=False) or not e.name.endswith('.json'):
                            continue
                        timestamp = datetime.fromtimestamp(e.stat(follow_symlinks=False).st_mtime)
                        if not start <= timestamp <= current:
                            continue
                        with open(e.path, encoding='utf-8') as fh:
                            m = json.load(fh)
                        if not isinstance(m, dict):
                            raise ValueError('non-object mission')
                        act = str(m.get('act') or '').lower()
                        src = _src(m.get('src'))
                        # m['ts'] is metadata; mtime is the required window filter.
                        if act in CHECKS or act.startswith('ro_'):
                            checks['failed' if failed else 'done'] += 1
                        else:
                            (fail if failed else sources)[src] += 1
                    except (OSError, ValueError, TypeError, OverflowError):
                        damage += 1
        except FileNotFoundError:
            pass
        except OSError:
            damage += 1

    if not notes and not answers and not sources and not fail and not checks:
        output = 'Heute habe ich dir noch nichts gemeldet und keine Aufträge ausgeführt.' if _intent(text) == 'today' else 'In den letzten 12 Stunden habe ich dir nichts gemeldet und keine Aufträge ausgeführt.'
        if damage:
            output += f' ({damage} fehlerhafte Einträge übersprungen.)'
        return output[:700]

    parts = []
    if notes:
        # JACK_TUNE_HEUTEGRUPPE (Claude 24.10.): gleiche Meldungsart (Ziffern egal) zusammenfassen, chronologisch
        groups = {}
        for ts, msg in sorted(notes, key=lambda n: n[0]):
            key = re.sub(r'\d+', '#', msg)[:40]
            g = groups.setdefault(key, [ts, ts, msg, 0])
            g[1], g[2], g[3] = ts, msg, g[3] + 1
        items = sorted(groups.values(), key=lambda g: g[0])
        parts.append('Meldungen: ' + '; '.join(
            g[1].strftime('%H:%M') + ' ' + g[2] + (' (%dx seit %s)' % (g[3], g[0].strftime('%H:%M')) if g[3] > 1 else '')
            for g in items[:6]))
        if len(items) > 6:
            parts.append(f'{len(items)-6} weitere Meldungsarten')
    if answers:
        parts.append(f'Telegram-Antworten: {answers}')
    if sources:
        parts.append('Aufträge erledigt: ' + ', '.join(f'{s} {n}' for s, n in sources.most_common(4)))
        if len(sources) > 4:
            parts.append(f'{len(sources)-4} weitere Quellen')
    if fail:
        parts.append('Aufträge fehlgeschlagen: ' + ', '.join(f'{s} {n}' for s, n in fail.most_common(3)))
    if checks:
        parts.append('Prüfabfragen: ' + str(checks.get('done', 0)) + ' ok, ' + str(checks.get('failed', 0)) + ' fehlgeschlagen')
    if damage:
        parts.append(f'{damage} fehlerhafte Einträge übersprungen')
    # Put summary ahead of verbose notifications so truncation never loses it.
    summary = [p for p in parts if not p.startswith('Meldungen:')]
    notification = [p for p in parts if p.startswith('Meldungen:')]
    return (intro + ': ' + ' | '.join(summary + notification))[:700]
