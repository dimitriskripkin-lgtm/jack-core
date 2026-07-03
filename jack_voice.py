#!/usr/bin/env python3
import os
import subprocess
import time
import re

JACK_HOME = os.path.expanduser("~/jack")
WHISPER_BIN = os.path.expanduser("~/whisper.cpp/build/bin/whisper-cli")
WHISPER_MODEL = os.path.expanduser("~/whisper.cpp/models/ggml-base.bin")
TMP_RAW = f"{JACK_HOME}/.voice_raw.wav"
TMP_FIXED = f"{JACK_HOME}/.voice_fixed.wav"

JA_WOERTER = ["ja", "jep", "jo", "mach", "okay", "ok", "los", "bestaetigt", "bestätigt"]
NEIN_WOERTER = ["nein", "ne", "stop", "stopp", "abbrechen", "nicht"]


def _cleanup():
    for f in (TMP_RAW, TMP_FIXED):
        if os.path.exists(f):
            os.remove(f)


def listen(seconds=5, lang="de"):
    _cleanup()
    subprocess.run(
        ["termux-microphone-record", "-f", TMP_RAW, "-e", "aac", "-r", "16000", "-l", str(seconds)],
        capture_output=True, timeout=10
    )
    time.sleep(seconds + 1)

    if not os.path.exists(TMP_RAW) or os.path.getsize(TMP_RAW) < 500:
        return ""

    conv = subprocess.run(
        ["ffmpeg", "-y", "-i", TMP_RAW, TMP_FIXED],
        capture_output=True, timeout=15
    )
    if conv.returncode != 0 or not os.path.exists(TMP_FIXED):
        return ""

    result = subprocess.run(
        [WHISPER_BIN, "-m", WHISPER_MODEL, "-f", TMP_FIXED, "-l", lang, "-nt"],
        capture_output=True, text=True, timeout=30
    )
    _cleanup()

    text = result.stdout.strip()
    text = "\n".join(line for line in text.split("\n") if line.strip())
    return text.strip().lower()


def speak(text):
    subprocess.run(["termux-tts-speak", "-l", "de", text], capture_output=True, timeout=15)


def confirm(prompt, seconds=4):
    speak(prompt)
    text = listen(seconds=seconds)

    if not text:
        return None

    for wort in JA_WOERTER:
        if re.search(r"\b" + re.escape(wort) + r"\b", text):
            return True
    for wort in NEIN_WOERTER:
        if re.search(r"\b" + re.escape(wort) + r"\b", text):
            return False
    return None


if __name__ == "__main__":
    print("[VOICE] Sprich jetzt (5 Sekunden) ...")
    txt = listen(5)
    print(f"[VOICE] Erkannt: '{txt}'")
    if txt:
        speak(f"Ich habe verstanden: {txt}")
