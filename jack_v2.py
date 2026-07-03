#!/data/data/com.termux/files/usr/bin/python3

import subprocess
import json
import time
import os

CONFIG_PATH = "/data/data/com.termux/files/home/jack/jack_config.json"

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def voice_record():
    print("🎤 JACK hört zu (8 Sekunden)... Sprich jetzt!")
    m4a_path = "/data/data/com.termux/files/home/j.m4a"
    wav_path = "/data/data/com.termux/files/home/j.wav"
    
    # Alte Dateien löschen
    for p in [m4a_path, wav_path]:
        if os.path.exists(p):
            os.remove(p)
    
    subprocess.run(["termux-microphone-record", "-l", "8", "-f", m4a_path], check=False)
    time.sleep(9)
    subprocess.run(["ffmpeg", "-i", m4a_path, "-ar", "16000", "-ac", "1", wav_path, "-y"], check=False)
    print("✅ Aufnahme fertig")
    return wav_path

def transcribe(wav_path):
    print("🧠 Whisper verarbeitet...")
    cmd = [
        "./whisper.cpp/build/bin/whisper-cli",
        "-m", "./whisper.cpp/models/ggml-base.bin",
        "-f", wav_path,
        "-l", "de",
        "-nt", "--no-timestamps",
        "-t", "6"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    text = result.stdout.strip()
    print("Erkannt:", text if text else "[nichts erkannt]")
    return text

print("🚀 JACK v2 – Verbesserte Version läuft")
config = load_config()
print("Config Version:", config["_meta"]["v"])

# Test
wav = voice_record()
text = transcribe(wav)
print("\n=== Endergebnis ===")
print("Du hast gesagt:", text)
