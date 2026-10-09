import re

def parse_and_prepare(resp, PENDING_EXEC, send_keyboard):
    """Prüft LLM-Antwort auf EXEC-Tags und bereitet Approval vor."""
    _cmd = None
    if '[[EXEC:' in resp:
        start = resp.find('[[EXEC:') + 7
        end = resp.find(']]', start)
        if end != -1: _cmd = resp[start:end].strip()
    elif '[[EXECUTE:' in resp:
        start = resp.find('[[EXECUTE:') + 10
        end = resp.find(']]', start)
        if end != -1: _cmd = resp[start:end].strip()
        
    if _cmd:
        # Halluzinierte SSH-Befehle bereinigen
        if 'sshpass' in _cmd or '10.229.239.131' in _cmd:
            match = re.search(r"'(am start.*?)'", _cmd)
            if match:
                _cmd = 'ssh xiaomi-jack su -c "' + match.group(1) + '"'
            else:
                _cmd = 'ssh xiaomi-jack su -c "' + _cmd.split()[-1].strip("'") + '"'
                
        PENDING_EXEC.clear()
        PENDING_EXEC['cmd'] = _cmd
        if len(_cmd) >= 800:  # JACK_TUNE_EXECLEN: lange Befehle nie halb sichtbar bestaetigen
            PENDING_EXEC.clear()
            send_keyboard('BEFEHL ABGELEHNT: %d Zeichen, Vorschau waere unvollstaendig. Bitte kuerzer.' % len(_cmd), [[('🔴 Schliessen', 'cancel_exec')]])
        else:
            send_keyboard('VORSCHLAG:' + chr(10) + _cmd, [[('🟢 Ausführen', 'run_exec'), ('🔴 Abbrechen', 'cancel_exec')]])
        
        # Tag aus Antwort entfernen
        resp = re.sub(r'\[\[EXEC(?:UTE)?:.*?\]\]', '', resp).strip()
        
    return resp
