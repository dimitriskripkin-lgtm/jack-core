#!/usr/bin/env python3
import subprocess
import threading
import os
import json

def transcribe_async(audio_path, callback=None):
    def _worker():
        if not os.path.exists(audio_path):
            print(f"[ERR] Audio file missing: {audio_path}")
            return
        try:
            cmd = ["whisper", audio_path, "--model", "tiny", "--output_format", "json"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            text = res.stdout.strip()
            if callback:
                callback(text)
        except Exception as e:
            print(f"[WARN] Async Whisper failed: {e}")

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t

if __name__ == "__main__":
    print("[OK] jack_whisper_async Modul bereit.")
