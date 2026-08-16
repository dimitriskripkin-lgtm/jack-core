#!/usr/bin/env python3
"""Entscheidet lokal oder Cloud. Regelbasiert - kein LLM-Call fuer die Entscheidung."""
import urllib.request

NUR_CLOUD = ('code','script','python','programmier','refactor','architektur',
             'debug','fehler analysier','warum funktioniert','erklaer mir wie',
             'philosoph','meinung','was denkst du','bild','foto')

LOKAL_GEEIGNET = ('klassifizier','ist das','ja oder nein','fass zusammen',
                  'wieviel','wie viele','zaehl','extrahier','uebersetze kurz')

def netz_da():
    for url in ['https://8.8.8.8','https://www.google.com','https://generativelanguage.googleapis.com']:
        try:
            urllib.request.urlopen(url, timeout=5)
            return True
        except Exception:
            pass
    return False

def route(prompt, aufgabe='allgemein'):
    """('lokal'|'cloud', begruendung)"""
    p = (prompt or '').lower()
    if aufgabe in ('code_pruefen','code_schreiben','architektur'):
        return 'cloud', 'Code und Architektur nie lokal'
    if not netz_da():
        return 'lokal', 'kein Netz - lokal ist die einzige Option'
    if any(w in p for w in NUR_CLOUD):
        return 'cloud', 'Aufgabe braucht echtes Reasoning'
    if any(w in p for w in LOKAL_GEEIGNET) and len(p) < 300:
        return 'lokal', 'einfache Aufgabe - spart API-Budget'
    if len(p) < 60 and '?' not in p:
        return 'lokal', 'kurzer Befehl'
    return 'cloud', 'Standard'

def denke(prompt, aufgabe='allgemein'):
    """Fuehrt aus - lokal oder Cloud - und sagt welches Gehirn geantwortet hat."""
    ziel, grund = route(prompt, aufgabe)
    if ziel == 'lokal':
        import jack_lokal as jl
        antwort, fehler = jl.frage(prompt, aufgabe)
        if antwort:
            return antwort, 'lokal (' + str(jl.aktiv()) + ')'
        if not netz_da():
            return 'Lokal ging nicht (' + str(fehler) + ') und kein Netz da.', 'keins'
        ziel = 'cloud'
    try:
        import jack_gemini_bridge as gb
        return gb.ask_gemini(prompt), 'cloud'
    except Exception as e:
        return 'Cloud-Fehler: ' + str(e)[:100], 'keins'

if __name__ == '__main__':
    import sys
    q = ' '.join(sys.argv[1:]) or 'Wieviel ist 12 mal 7?'
    z, g = route(q)
    print('Route: ' + z + ' (' + g + ')')
    print('Netz: ' + ('ja' if netz_da() else 'nein'))
