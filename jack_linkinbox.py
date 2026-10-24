#!/usr/bin/env python3
"""JACK_TUNE_LINKINBOX (Kap 302, 23.10.2026): Video-/Social-Links aus Telegram sammeln.
Dima teilt ein Video (TikTok, Instagram, YouTube, X, Facebook) an den JACK-Bot -> Zeile in logs/link_inbox.jsonl.
Claude/ChatGPT lesen die Datei per MCP (read_file) und werten den Link mit Supadata aus.
JACK ruft Supadata NICHT selbst auf (kein Key auf dem Geraet, keine Credits ohne Dima).
Andere Links laufen weiter ueber jack_web_ingest. /links zeigt die letzten 5.
"""
import json, os, re, time

DATEI = '/data/data/com.termux/files/home/jack/logs/link_inbox.jsonl'
MUSTER = re.compile(r'https?://(?:[\w-]+\.)*(?:tiktok\.com|instagram\.com|youtube\.com|youtu\.be|x\.com|twitter\.com'
                    r'|facebook\.com|fb\.watch)/[^\s<>"]+', re.I)


def finde(text):
    return [u.rstrip('.,;:!?)]') for u in MUSTER.findall(str(text or ''))]


def _kurz(u):
    return re.sub(r'^https?://(www\.|m\.)?', '', u)[:60]


def merke(text, quelle='telegram'):
    """Gibt Antworttext zurueck, wenn etwas gemerkt wurde (oder /links), sonst None."""
    t = str(text or '').strip()
    if t.lower().startswith('/links'):
        return letzte()
    links = finde(t)
    if not links:
        return None
    notiz = MUSTER.sub('', t).strip()[:300]
    jetzt = time.strftime('%Y-%m-%d %H:%M:%S')
    os.makedirs(os.path.dirname(DATEI), exist_ok=True)
    with open(DATEI, 'a') as fh:
        for u in links:
            fh.write(json.dumps({'ts': jetzt, 'url': u, 'notiz': notiz, 'quelle': quelle, 'status': 'neu'},
                                ensure_ascii=False) + '\n')
    return '📥 Für Claude gemerkt (%d): %s\nSag Claude einfach "guck Inbox".' % (
        len(links), ', '.join(_kurz(u) for u in links))


def letzte(n=5):
    try:
        with open(DATEI) as fh:
            zeilen = [json.loads(z) for z in fh if z.strip()]
    except OSError:
        return 'Link-Inbox ist leer.'
    if not zeilen:
        return 'Link-Inbox ist leer.'
    return 'Letzte Links:\n' + '\n'.join('%s %s' % (z['ts'][5:16], _kurz(z['url'])) for z in zeilen[-n:])


if __name__ == '__main__':
    import sys
    print(merke(' '.join(sys.argv[1:])) if len(sys.argv) > 1 else letzte())
