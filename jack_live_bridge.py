#!/usr/bin/env python3
import os
import sys
import time
import asyncio
import subprocess
import configparser

JACK_DIR = os.path.expanduser("~/jack")
sys.path.insert(0, JACK_DIR)

import jack_whisper_async as whisper
import jack_groq_bridge as groq

RECORD_FILE = os.path.expanduser("$PREFIX/tmp/jack_live_input.wav")
RESPONSE_AUDIO = os.path.expanduser("$PREFIX/tmp/jack_live_out.mp3")

class JACKLiveVoiceBridge:
    def __init__(self):
        self.is_running = False

    def record_chunk(self, duration=3):
        """Nimmt kurz Audio über Termux-API auf."""
        try:
            cmd = f"termux-microphone-record -f {RECORD_FILE} -l {duration} -r 16000 -c 1"
            subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(duration + 0.2)
            return os.path.exists(RECORD_FILE) and os.path.getsize(RECORD_FILE) > 1000
        except Exception:
            return False

    async def speak(self, text):
        """Audio-Antwort ausgeben."""
        print(f"\n[JACK]: {text}")
        # Einfacher TTS Fallback / System Player
        tts_cmd = f"espeak-ng -v de \"{text}\" --stdout | mpv - --really-quiet"
        subprocess.run(tts_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    async def run_loop(self):
        self.is_running = True
        print("=== JACK LIVE VOICE BRIDGE ACTIVE ===")
        print("[INFO] Sprich nach dem Signal... (STRG+C zum Beenden)")
        
        while self.is_running:
            try:
                print("\n[LISTENING...]", end="", flush=True)
                has_audio = self.record_chunk(duration=3)
                
                if not has_audio:
                    continue

                print(" -> [PROCESSING]", end="", flush=True)
                # STT via Whisper
                user_text = await whisper.transcribe_audio(RECORD_FILE)
                if not user_text or len(user_text.strip()) < 2:
                    continue

                print(f"\n[DIMA]: {user_text}")

                # Fast LLM Response via Groq
                response_text = await groq.query_groq(user_text)
                if response_text:
                    await self.speak(response_text)

            except KeyboardInterrupt:
                print("\n[INFO] Live Voice Bridge gestoppt.")
                self.is_running = False
                break
            except Exception as e:
                print(f"\n[ERR] Loop Error: {e}")
                await asyncio.sleep(1)

if __name__ == "__main__":
    bridge = JACKLiveVoiceBridge()
    asyncio.run(bridge.run_loop())
