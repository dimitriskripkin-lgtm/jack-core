"""JACK_TUNE_TATENWAHRHEIT (27.10.2026, Kap 04; Entwurf ChatGPT S2, Abnahme Claude mit Feldfall-Fixes).
S2: Guard gegen unbelegte AKTUELLE Erfolgsmeldungen von TALK.
Kein I/O oder Modellaufruf. verified_actions darf nur der Aktions-Dispatcher setzen.
"""
import re

_ACTIONS = {
    'play': r'(?:gestartet|abgespielt|angemacht|eingeschaltet|wiedergegeben)',
    'save': r'(?:gespeichert|abgelegt|eingetragen|hinzugefuegt|hinzugefügt|notiert)',
    'close': r'(?:geschlossen|beendet|gestoppt|gelöscht|geloescht|entfernt)',
    'send': r'(?:gesendet|verschickt|veröffentlicht|veroeffentlicht|übertragen|uebertragen)',
    'check': r'(?:geprüft|geprueft|gemessen|kontrolliert)',
}
_VERBS = '|'.join('(?:'+x+')' for x in _ACTIONS.values())
_FIRST = re.compile(r'\b(?:ich|wir|jack)\s+(?:habe|hab|haben|hat|hätten|haetten)\b', re.I)  # Claude: +hab
_INVERT = re.compile(r'\b(?:habe|hab|haben|habs|hab\'s)\s+(?:ich|wir)\b|^\s*(?:hab|habe|habs|hab\'s)\b', re.I)  # Claude: Umgangssprache
_PASSIVE = re.compile(r'\b(?:wurde|wurden|ist|sind)\s+.{0,95}?\b(?:'+_VERBS+r')\b', re.I)
_DONE = re.compile(r'\b(?:ist|wäre|waere)\s+(?:bereits\s+)?erledigt\b|\b(?:hab|habe|habs|hab\'s)\s+(?:ich\s+)?(?:es\s+|das\s+)?(?:schon\s+)?erledigt\b|\bauftrag\s+(?:abgeschlossen|erledigt)\b', re.I)
_NEGATION = re.compile(r'\b(?:nicht|nie|kein|keine|keinen|ohne|noch\s+nicht)\b', re.I)
_HYPOTHETIC = re.compile(r'\b(?:wenn|falls|würde|wuerde|wäre|waere|könnte|koennte|sollte|möchte|moechte|hätte|haette|angenommen|beispiel|hypothetisch)\b', re.I)
_PAST = re.compile(r'\b(?:gestern|vorgestern|damals|früher|frueher|letzte\s+woche|1\d{3}|20\d{2}|vor\s+\d+\s+(?:tagen|monaten|jahren))\b', re.I)
_ACTION_RX = {k: re.compile(r'\b'+v+r'\b',re.I) for k,v in _ACTIONS.items()}
_GENERIC = re.compile(r'\b(?:das|es|alles)\s+(?:ist|wurde)\s+(?:jetzt\s+)?(?:erledigt|fertig|abgeschlossen)\b',re.I)
_NOW = re.compile(r'(?:\b(?:jetzt|gerade|soeben|eben|erfolgreich|sofort|für\s+(?:dich|claude|dima)|fuer\s+(?:dich|claude|dima))\b|✅)', re.I)
_ITEM = re.compile(r'\b(?:musik|track|song|lied|titel|playlist|akku|app|apps|datei|dateien|chrome|spotify|link|links|nachricht|termin|timer|wecker|alarm|xiaomi|honor|handy|befehl|mission|notiz)\b', re.I)
_QUOTE_START = re.compile(r'^\s*(?:[„\"\']|>|beispiel\s*:|zitat\s*:)',re.I)


def _sentences(s):
    """Nicht an Punkten in Dateinamen/Zahlen trennen; Satzzeichen bewahren."""
    return re.split(r'(?<=[!?;])\s+|(?<=[.])\s+(?=[A-ZÄÖÜ„✅])|,\s*(?=(?:wenn|falls)\b)', str(s))  # Claude: +; und ', wenn'


def _classify(sentence):
    t=sentence.strip()
    if not t or t.endswith("?") or _QUOTE_START.search(t) or _HYPOTHETIC.search(t) or _PAST.search(t):
        return None
    # Explizit verneinte Aktionen sind gerade KEINE Erfolgsbehauptung.
    if _NEGATION.search(t):return None
    if _GENERIC.search(t) or _DONE.search(t):return 'generic'
    # JACK_TUNE_Z1C_S2MUSIK: unbelegte Musik-Imperative nicht als erledigt melden.
    if (re.match(r'^\s*(?:spiel(?:e)?|start(?:e)?|spring(?:e)?|skip(?:pe)?|wechsel(?:e)?|ueberspring(?:e)?|überspring(?:e)?)\b', t, re.I)
            and re.search(r'\b(?:spotify|musik|titel|track|song|lied|playlist)\b', t, re.I)
            and (_NOW.search(t) or re.search(r'\berledigt\b', t, re.I))):
        return 'play'
    _pas = _PASSIVE.search(t) and (_NOW.search(t) or _ITEM.search(t))  # Claude: Passiv nur mit Jetzt-Bezug oder JACK-Geraete-/App-Objekt
    if not (_FIRST.search(t) or _INVERT.search(t) or _pas):
        return None
    # 'Ich habe dich verstanden' enthaelt kein Aktionsverb.
    for kind,rx in _ACTION_RX.items():
        if rx.search(t):return kind
    return None


def sanitize(text, verified_actions=()):
    """Entferne nur unbelegte aktuelle Erfolgssaetze; andere Saetze bleiben erhalten.

    verified_actions: iterable of trusted RECEIPT classes ('play','save','close','send').
    Das Modell darf solche Belege niemals selbst anliefern.
    """
    if not isinstance(text,str):text=str(text or '')
    verified=set(verified_actions or ())
    output=[];removed=[]
    for sentence in _sentences(text):
        kind=_classify(sentence)
        if kind and (kind=='generic' or kind not in verified):
            removed.append(kind)
        else:output.append(sentence)
    if not removed:return text
    prefix=' '.join(x.strip() for x in output if x.strip())
    safe='Das habe ich hier nicht ausgeführt. Für eine echte Aktion brauche ich einen passenden JACK-Befehl und dessen bestätigtes Ergebnis.'
    return ((prefix+' ') if prefix else '')+safe


def repeat_reference(text):
    """Satz verweist auf eine vorherige Aktion; NICHT automatisch ausführen."""
    if not isinstance(text,str):return False
    return bool(re.search(r'\b(?:dasselbe|das\s+gleiche|nochmal|noch\s+mal|wiederhol(?:en|e)?|auch\s+auf\s+(?:dem\s+)?(?:honor|xiaomi))\b',text,re.I))
