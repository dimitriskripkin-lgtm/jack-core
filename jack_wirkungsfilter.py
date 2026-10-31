"""JACK_TUNE_Z1_WIRKUNG - Entwurf, NUR fuer ungepruefte TALK-Antworten.
Schneidet aktuelle unbelegte Erfolg-/Wirkungsaussagen ueber JACK heraus.
Kein IO, kein Modell, kein Vertrauen in vom LLM gelieferte Belege.
"""
import re

DOMAIN = re.compile(
    r'\b(?:jack|honor|xiaomi|n8n|telegram|spotify|kalender|'
    r'sicherung|backup|restore|wiederherstellung|dienst(?:e)?|'
    r'fehler|fehlerquote|erfolgsquote|ausfallrate|bug|problem|patch|fix|aenderung|änderung|'
    r'system|funktion|skript|script|mission|prozess|code|'
    r'workflow|schnittstelle|verbindung|tunnel|datenbank|'
    r'modul(?:e|en)?|einsatz|'
    r'ssh|routen?|konnektivitaet|konnektivität|netz|leistung|performance|geschwindigkeit)\b', re.I)
CURRENT = re.compile(r'\b(?:jetzt|nun|ab\s+sofort|seit\s+dem\s+fix|'
                     r'ab\s+heute|wieder|inzwischen|dadurch|damit)\b', re.I)
PROVED = re.compile(
    r'\b(?:garantiert|nachgewiesen|bewiesen|verifiziert|bestaetigt|bestätigt|'
    r'endgueltig|endgültig|dauerhaft|hundertprozentig|100\s*%|'
    r'fehlerfrei|ausfallsicher|zuverlaessig|zuverlässig|stabil|'
    r'vollstaendig\s+behoben|vollständig\s+behoben|'
    r'problemlos|sichergestellt)\b', re.I)
OUTCOME = re.compile(
    r'\b(?:laeuft|läuft|funktioniert|klappt|arbeitet|ist|sind|wurde|wurden|'
    r'bleibt|bleiben|hat|haben|bietet|liefert|verhindert|schuetzt|schützt)\b', re.I)
NO_MORE = re.compile(r'\b(?:keine?\s+(?:fehler|bugs|probleme|ausfaelle|ausfälle)\s+mehr|'
                     r'nie\s+wieder\s+(?:ausfaelle|ausfälle|fehler))\b', re.I)
QUANTIFIED = re.compile(r'\b(?:\d+(?:[,.]\d+)?\s*%\s*(?:schneller|besser|'
                       r'zuverlaessiger|zuverlässiger|weniger\s+fehler)|'
                       r'(?:erfolgsquote|fehlerquote|ausfallrate)\s*'
                       r'(?:ist\s+)?(?:von|auf|um)\s*\d+(?:[,.]\d+)?\s*%)(?=$|[^a-z0-9_])', re.I)
EXCLUDE = re.compile(r'\b(?:wenn|falls|könnte|koennte|würde|wuerde|'
                     r'möglicherweise|moeglicherweise|vielleicht|vermutlich|'
                     r'angenommen|hypothetisch|nicht\s+belegt|unbewiesen|'
                     r'noch\s+nicht\s+bewiesen)\b', re.I)
HISTORIC = re.compile(r'\b(?:damals|frueher|früher|gestern|vorgestern|'
                      r'letzte\s+woche|vor\s+\d+\s+(?:tagen|monaten|jahren))\b', re.I)


def sentences(text):
    return re.split(r'(?<=[!?;])\s+|(?<=\.)\s+(?=[A-ZÄÖÜ„])', text)


EFFECT_PRESENT = re.compile(
    r'\b(?:verbesser(?:e|t|n)|beschleunig(?:e|t|en)|stabilisier(?:e|t|en)|'
    r'erh(?:oe|ö|o)h(?:e|t|en)|senk(?:e|t|en)|steiger(?:e|t|n))\b', re.I)
INTENSITY = re.compile(r'\b(?:spuerbar|spürbar|deutlich|merklich)\b', re.I)

def unverified_effect(sentence):
    t = sentence.strip()
    if not t or t.endswith('?') or t.startswith(('>', '„', '"', "'")):
        return False
    if EXCLUDE.search(t) or HISTORIC.search(t) or re.search(r'\b(?:könnten|koennten|sollten)\b', t, re.I):
        return False
    # JACK_TUNE_Z1D: pauschale, aktuelle Erfolgsaussage ohne Messbeleg
    # bewusst keine Einzelfall-Statussaetze wie "Musik pause ... pausiert".
    if (re.search(r'\b(?:alles|komplett|ueberall|überall)\b', t, re.I)
            and re.search(r'\b(?:laeuft|läuft|funktioniert)\b', t, re.I)
            and re.search(r'\b(?:stabil|einwandfrei|perfekt)\b', t, re.I)):
        return True
    if not DOMAIN.search(t):
        return False
    # Objektiver Zugewinn an Zuverlaessigkeit/Stabilitaet/Sicherheit
    # ohne bestaetigenden Test ist keine belegte Wirkung.
    if (re.search(r'\b(?:modul(?:e|en)?|einsatz)\b', t, re.I)
            and re.search(r'\b(?:erhoehen|erhöhen|erhoeht|erhöht|steigern|steigert)\b', t, re.I)
            and re.search(r'\b(?:zuverlaessigkeit|zuverlässigkeit|stabilitaet|stabilität|sicherheit)\b', t, re.I)):
        return True
    if re.search(r'\b100\s*%\s*(?:sicher|fehlerfrei|zuverlaessig|zuverlässig)\b', t, re.I):
        return True
    if re.search(r'\bist\s+jetzt\s+sicher\b', t, re.I):
        return True
    if EFFECT_PRESENT.search(t) and (INTENSITY.search(t) or CURRENT.search(t)):
        return True
    if QUANTIFIED.search(t) or NO_MORE.search(t) or re.search(r'\bverhindert\b.{0,35}\b(?:alle|jeden|saemtliche|sämtliche)\s+(?:fehler|bugs|ausfaelle|ausfälle)\b',t,re.I):
        return True
    if PROVED.search(t) and OUTCOME.search(t):
        return True
    # Keine freie Tatsachenpruefung, nur aktuelle, klar abgegrenzte Claims.
    if CURRENT.search(t) and re.search(r'\b(?:geloest|gelöst|behoben|repariert|'
                                        r'optimiert|beschleunigt|verbessert|verbessern|verbessere|stabilisiert|stabilisieren|erhöht|erhoeht|senkt)\b', t, re.I):
        return True
    return False


def sanitize(text):
    """Keine Belegparameter aus LLM-Antworten akzeptieren; nur Postfilter."""
    text = str(text or '')
    parts = sentences(text)
    kept = [p for p in parts if not unverified_effect(p)]
    if len(kept) == len(parts):
        return text
    base = ' '.join(p.strip() for p in kept if p.strip())
    caution = 'Diese Wirkung kann ich ohne aktuellen Test oder Messbeleg nicht bestätigen.'
    return (base + ' ' if base else '') + caution
