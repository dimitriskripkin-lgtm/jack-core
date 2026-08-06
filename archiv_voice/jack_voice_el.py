#!/usr/bin/env python3
import os
import subprocess
import sys

try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import stream
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False

API_KEY = os.environ.get("ELEVENLABS_API_KEY")
VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
MODEL_ID = "eleven_flash_v2_5"


def _fallback_speak(text):
    subprocess.run(["termux-tts-speak", "-l", "de", text], capture_output=True, timeout=15)


def speak(text, voice_id=None, force_local=False):
    if force_local or not ELEVENLABS_AVAILABLE or not API_KEY:
        _fallback_speak(text)
        return
    try:
        client = ElevenLabs(api_key=API_KEY)
        audio_stream = client.text_to_speech.stream(
            text=text,
            voice_id=voice_id or VOICE_ID,
            model_id=MODEL_ID,
        )
        stream(audio_stream)
    except Exception as e:
        print(f"[VOICE_EL] ElevenLabs Fehler ({e}), falle zurueck auf lokales TTS", file=sys.stderr)
        _fallback_speak(text)


if __name__ == "__main__":
    if not API_KEY:
        print("[VOICE_EL] ELEVENLABS_API_KEY nicht gesetzt, teste Fallback...")
        speak("Test. Kein API Key gefunden, lokales TTS aktiv.", force_local=True)
    else:
        print(f"[VOICE_EL] Teste ElevenLabs Streaming (Voice: {VOICE_ID})...")
        speak("Hallo Dimitri. Ich bin JACK. Test der neuen Stimme.")
