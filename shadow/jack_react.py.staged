import os, sys
sys.path.insert(0, os.path.expanduser('~/jack'))

def analysiere(cmd, output):
    try:
        import jack_gemini_bridge as gb
        frage = ('Dieser Shell-Befehl auf Android/Termux schlug fehl.'
                 + chr(10) + 'BEFEHL:' + chr(10) + cmd[:800]
                 + chr(10) + 'OUTPUT:' + chr(10) + output[:1200]
                 + chr(10) + chr(10)
                 + 'Antworte in maximal 3 Zeilen: 1) Ursache in einem Satz. '
                 + '2) Korrigierter Befehl als reine Shell-Zeile ohne Markdown. '
                 + 'Regeln: kein /tmp, kein ping, Pfade unter ~/jack. '
                 + 'Wenn kein sicherer Fix moeglich ist, schreibe nur KEIN_FIX.')
        return gb.ask_gemini(frage, {})
    except Exception as e:
        return 'Analyse fehlgeschlagen: ' + str(e)[:150]
