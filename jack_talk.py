#!/usr/bin/env python3
import sys
import time
from datetime import datetime

sys.path.insert(0, "/data/data/com.termux/files/home/jack")

from jack_voice import listen
from jack_voice_el import speak as speak_el
import jack_memory

EXIT_WOERTER = ["jack stop", "beenden", "schluss", "tschuess", "tschüss"]


def _ts():
    return datetime.now().strftime("%H:%M:%S")


def talk_loop(listen_seconds=5):
    speak_el("Ich hoere zu.")
    print(f"[{_ts()}] [TALK] Loop gestartet. Sag 'jack stop' zum Beenden.\n")

    while True:
        print(f"[{_ts()}] [TALK] Höre {listen_seconds}s zu...")
        text = listen(seconds=listen_seconds)

        if not text:
            print(f"[{_ts()}] [TALK] Nichts verstanden, naechster Versuch.\n")
            continue

        print(f"[{_ts()}] [TALK] Du: {text}")

        if any(exit_wort in text for exit_wort in EXIT_WOERTER):
            speak_el("Bis später, Dimitri.")
            print(f"[{_ts()}] [TALK] Beendet.")
            break

        antwort = f"Ich habe verstanden: {text}"
        print(f"[{_ts()}] [TALK] JACK: {antwort}\n")
        speak_el(antwort)

        try:
            jack_memory.save(text, antwort, intent="voice_chat")
        except Exception as e:
            print(f"[{_ts()}] [TALK] Memory-Save fehlgeschlagen: {e}")

        time.sleep(0.5)


if __name__ == "__main__":
    talk_loop()
