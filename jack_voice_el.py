#!/usr/bin/env python3
"""Stub fuer jack_voice_el (ElevenLabs Voice).
Ersetzt fehlendes Modul damit jack_talk importierbar bleibt.
Echte Implementierung bei Bedarf: elevenlabs API + Termux-Audio."""
def speak(text, voice_id=None, model=None):
    """Spricht Text via ElevenLabs. Stub: gibt nur auf stdout aus."""
    try:
        import jack_log; jack_log.log_decision("VOICE-EL-STUB", str(text)[:80])
    except Exception:
        pass
    print(f"[VOICE-EL-STUB] {text}")
    return False

def is_available():
    return False
