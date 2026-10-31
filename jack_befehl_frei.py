"""JACK Block E: deterministischer Freitext-Router, NUR bekannte Befehle.
Kein I/O. /akku, /standort und /lage sind Xiaomi-Abfragen.
/Timer ist HONOR per Default und akzeptiert explizit 'xiaomi'.
"""
import re


def frei(text):
    if str(text or '').lstrip().startswith('/'):
        return None  # explizite Slash-Befehle nicht umdeuten
    t = str(text or '').lower()
    for a, b in (('ä','ae'), ('ö','oe'), ('ü','ue'), ('ß','ss')):
        t = t.replace(a,b)
    t = ' '.join(re.findall(r'[a-z0-9]+', t))
    if not t or t.startswith('slash '):
        return None
    t = re.sub(r'^(?:jack\s+)?(?:bitte\s+)?', '', t)
    t = re.sub(r'\s+(?:bitte|jetzt)$', '', t)
    # Keine Umdeutung von ausdruecklich auf HONOR bezogenen Xiaomi-Abfragen.
    honor = bool(re.search(r'\b(?:honor|mein honor|dem honor)\b',t))
    xiaomi = bool(re.search(r'\bxiaomi\b',t))
    q = re.sub(r'\s+(?:auf|am|vom|von dem)\s+(?:dem\s+)?xiaomi\b','',t)
    q = re.sub(r'\s+xiaomi\b','',q).strip()
    q = re.sub(r'\s+(?:auf|am|vom|von dem)\s+(?:dem\s+)?honor\b','',q).strip()

    # Timer: volle Ankerphrase; einheitenbasiert; freie Restbeschreibung nur nach 'fuer'.
    tm = re.fullmatch(
        r'(?:(?:stell(?:e)?\s+(?:mir\s+)?(?:einen\s+)?)|(?:starte?\s+(?:mir\s+)?(?:einen\s+)?)|(?:mach(?:e)?\s+(?:mir\s+)?(?:einen\s+)?))?'
        r'timer\s+(?:auf\s+|fuer\s+|von\s+)?'
        r'(\d{1,4}(?:[.,]\d+)?)\s*(sekunden?|sek|s|minuten?|min|m|stunden?|std|h)'
        r'(?:\s+fuer\s+([a-z0-9][a-z0-9 ]{0,60}))?',q)
    if tm:
        number=float(tm.group(1).replace(',','.'))
        unit=tm.group(2)
        sec=number*(1 if unit.startswith(('sek','s')) and unit not in ('stunden','stunde','std') else 3600 if unit.startswith(('stunde','std','h')) else 60)
        if 1<=sec<=86400:
            short='s' if unit.startswith(('sek','s')) and not unit.startswith(('stunde','std')) else 'h' if unit.startswith(('stunde','std','h')) else 'm'
            cmd='/timer '+tm.group(1)+short
            if tm.group(3):cmd+=' '+tm.group(3)
            return cmd+(' xiaomi' if xiaomi else '')
        return None
    if honor:
        return None
    if re.fullmatch(r'(?:akku|akkustand|batteriestand|akku stand|akku status|wie voll ist (?:mein|der|dein) akku|wie (?:viel|viele) (?:prozent|akku) (?:hat|habe|hab) (?:ich|mein handy|das handy|der akku)|(?:zeige?|zeig mir|sag mir) (?:den|meinen)? ?(?:akku|akkustand)|(?:wie ist|was ist) (?:der|mein)? ?akkustand)',q):
        return '/akku'
    if re.fullmatch(r'(?:standort|gps standort|wo ist (?:mein|das) xiaomi|wo befindet sich (?:mein|das) xiaomi|(?:zeige?|zeig mir|sag mir) (?:den|meinen)? ?standort|(?:was ist|wie ist) (?:der|mein)? ?standort)',t if 'wo ist' in t or 'wo befindet' in t else q):
        return '/standort'
    if re.fullmatch(r'(?:lage|xiaomi lage|(?:zeige?|zeig mir|sag mir) (?:die )?lage|wie ist die lage|was ist die lage|lagebericht|wie sieht die lage aus)',q):
        return '/lage'
    return None
