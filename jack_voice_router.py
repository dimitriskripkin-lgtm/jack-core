#!/usr/bin/env python3
"""JACK Voice Router: Vollständiger Dispatcher für Stack A (Gemini Live) und Stack B (Offline).
Mit Live-Streaming-Support für mpv."""
import os, sys, time, urllib.request, subprocess, asyncio, wave, struct

sys.path.append(os.path.expanduser("~/jack"))
API_CHECK_URL = "https://www.google.com/generate_204"
API_TIMEOUT = 2.0

def check_connectivity():
    try:
        urllib.request.urlopen(API_CHECK_URL, timeout=API_TIMEOUT)
        return True
    except Exception:
        return False

def write_wav_header(f, sample_rate=24000, channels=1, sample_width=2):
    """Schreibt einen minimalen WAV-Header für Streaming."""
    f.write(b'RIFF')
    f.write(struct.pack('<I', 0xFFFFFFFF))  # Unbekannte Größe (Streaming)
    f.write(b'WAVE')
    f.write(b'fmt ')
    f.write(struct.pack('<I', 16))  # Chunk-Größe
    f.write(struct.pack('<H', 1))   # PCM format
    f.write(struct.pack('<H', channels))
    f.write(struct.pack('<I', sample_rate))
    f.write(struct.pack('<I', sample_rate * channels * sample_width))
    f.write(struct.pack('<H', channels * sample_width))
    f.write(struct.pack('<H', sample_width * 8))
    f.write(b'data')
    f.write(struct.pack('<I', 0xFFFFFFFF))  # Unbekannte Größe (Streaming)

def tts_espeak(text, wav_out):
    """Offline TTS mit espeak."""
    try:
        subprocess.run(["espeak", "-v", "de", "-w", wav_out, text], capture_output=True, check=True)
        return os.path.exists(wav_out) and os.path.getsize(wav_out) > 100
    except Exception:
        return False

def play_audio(wav_path):
    """Fallback: Spielt eine WAV-Datei ab."""
    try:
        size = os.path.getsize(wav_path)
        duration = max(1, int(size / 48000) + 1)
        subprocess.run(["termux-media-player", "play", wav_path], capture_output=True)
        time.sleep(duration)
    except Exception:
        pass

async def process_stack_a_live_stream(audio_path):
    """Stream Audio in Echtzeit über mpv."""
    print("[ROUTER] Stack A: Live-Streaming via mpv...")
    
    # PCM-Datei erstellen
    base_name = os.path.splitext(audio_path)[0]
    pcm_path = base_name + ".pcm"
    
    try:
        subprocess.run(["ffmpeg", "-y", "-i", audio_path, "-ar", "16000", "-ac", "1", "-f", "s16le", pcm_path], capture_output=True, check=True)
    except Exception as e:
        print(f"[ROUTER] FFmpeg-Fehler: {e}")
        return False, None
    
    # mpv-Prozess starten
    mpv_process = subprocess.Popen(
        ["mpv", "--no-video", "--demuxer=rawaudio", "--demuxer-rawaudio-rate=24000", "--demuxer-rawaudio-channels=1", "-"],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    if not mpv_process.stdin:
        print("[ROUTER] mpv konnte nicht gestartet werden")
        return False, None
    
    
    # Audio-Chunks in Echtzeit empfangen und an mpv streamen
    chunk_count = 0
    first_chunk_time = None
    
    async def audio_callback(chunk):
        nonlocal chunk_count, first_chunk_time
        if first_chunk_time is None:
            first_chunk_time = time.time()
        mpv_process.stdin.write(chunk)
        mpv_process.stdin.flush()
        chunk_count += 1
    
    # Import und Streaming-Aufruf
    try:
        import jack_voice_live as vl
        if hasattr(vl, 'voice_stream'):
            success = await vl.voice_stream(pcm_path, audio_callback)
            
            # mpv beenden
            mpv_process.stdin.close()
            mpv_process.wait()
            
            if success and chunk_count > 0:
                print(f"[ROUTER] Live-Streaming erfolgreich: {chunk_count} Chunks")
                return True, None
    except Exception as e:
        print(f"[ROUTER] Streaming-Fehler: {type(e).__name__} - {str(e)[:100]}")
        mpv_process.stdin.close()
        mpv_process.wait()
    
    return False, None

async def process_stack_a_live(audio_path):
    """Fallback: Sammelt Audio und spielt es am Ende ab."""
    print("[ROUTER] Stack A: Versuche Gemini Live API (klassisch)...")
    try:
        import jack_voice_live as vl
        if hasattr(vl, 'voice_roundtrip'):
            base_name = os.path.splitext(audio_path)[0]
            pcm_path = base_name + ".pcm"
            
            subprocess.run(["ffmpeg", "-y", "-i", audio_path, "-ar", "16000", "-ac", "1", "-f", "s16le", pcm_path], capture_output=True, check=True)
            
            first_ms, chunks = await vl.voice_roundtrip(pcm_path)
            if chunks and first_ms is not None:
                wav_out = base_name + "_resp.wav"
                with wave.open(wav_out, "wb") as w:
                    w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000)
                    w.writeframes(b"".join(chunks))
                print(f"[ROUTER] Stack A ERFOLGREICH: Antwort in {int(first_ms)}ms, gespeichert unter {wav_out}")
                return True, wav_out
        print("[ROUTER] Stack A FEHLGESCHLAGEN: Keine Chunks erhalten.")
        return False, None
    except Exception as e:
        print(f"[ROUTER] Stack A FEHLER: {type(e).__name__} - {str(e)[:100]}")
        return False, None

async def process_stack_b_offline(audio_path):
    """Stack B: 100% Offline-Fallback (Whisper + Ollama + espeak)"""
    print("[ROUTER] Stack B: 100% Offline-Fallback (Whisper + Ollama + espeak)...")
    base_name = os.path.splitext(audio_path)[0]
    wav_in = base_name + "_stt.wav"
    wav_out = base_name + "_tts.wav"
    
    # 1. STT: Whisper lokal
    try:
        subprocess.run(["ffmpeg", "-y", "-i", audio_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", wav_in], capture_output=True, check=True)
        whisper_path = os.path.expanduser("~/whisper.cpp/build/bin/whisper-cli")
        model_path = os.path.expanduser("~/whisper.cpp/models/ggml-small.bin")
        if not os.path.exists(whisper_path) or not os.path.exists(model_path):
            print("[ROUTER] Stack B FEHLER: whisper.cpp nicht installiert")
            return None, "Whisper fehlt"
        result = subprocess.run([whisper_path, "-m", model_path, "-f", wav_in, "-l", "de", "-nt", "-t", "4"], capture_output=True, text=True)
        text = " ".join(result.stdout.split()).strip()
        if not text:
            print("[ROUTER] Stack B: Whisper hat nichts erkannt")
            return None, "Kein Text erkannt"
        print(f"[ROUTER] Stack B STT: '{text}'")
    except Exception as e:
        print(f"[ROUTER] Stack B STT-Fehler: {e}")
        return None, f"STT-Fehler: {e}"
    
    # 2. LLM: Ollama lokal
    try:
        import json as _json
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5) as r:
            models = _json.loads(r.read().decode())["models"]
        model = next((m["name"] for m in models if "embed" not in m["name"].lower()), "llama3.2:3b")
        req = urllib.request.Request(
            "http://localhost:11434/api/chat",
            data=_json.dumps({"model": model, "messages": [{"role": "user", "content": text}], "stream": False}).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = _json.loads(resp.read().decode())
        reply = data["message"]["content"].strip()
        if not reply:
            reply = text
        print(f"[ROUTER] Stack B LLM ({model}): '{reply[:80]}'")
    except Exception as e:
        print(f"[ROUTER] Stack B LLM-Fehler: {e}, verwende Originaltext")
        reply = text
    
    # 3. TTS: espeak lokal
    if tts_espeak(reply, wav_out):
        print(f"[ROUTER] Stack B ERFOLGREICH: Offline-Antwort erzeugt")
        return reply, wav_out
    else:
        print("[ROUTER] Stack B TTS-Fehler: espeak fehlgeschlagen")
        return reply, None


async def route_voice(audio_path):
    if not os.path.exists(audio_path):
        return {"success": False, "error": "Datei nicht gefunden"}

    print(f"[ROUTER] Starte Routing für: {audio_path} ({os.path.getsize(audio_path)} Bytes)")
    
    if check_connectivity():
        print("[ROUTER] Internet verfügbar. Prüfe Stack A...")
        
        # Versuche Live-Streaming
        success, wav_out = await process_stack_a_live_stream(audio_path)
        if success:
            return {"success": True, "stack": "A", "stream": True}
        
        # Fallback zu klassischer Methode
        print("[ROUTER] Live-Streaming fehlgeschlagen, versuche klassische Methode...")
        success, wav_out = await process_stack_a_live(audio_path)
        if success:
            play_audio(wav_out)
            return {"success": True, "stack": "A", "audio": wav_out}
        
        print("[ROUTER] Stack A fehlgeschlagen. Wechsle zu Stack B.")
    else:
        print("[ROUTER] Kein Internet. Direkter Wechsel zu Stack B.")
        
    text, audio_or_error = await process_stack_b_offline(audio_path)
    if text:
        if audio_or_error and os.path.exists(audio_or_error):
            play_audio(audio_or_error)
            return {"success": True, "stack": "B", "text": text, "audio": audio_or_error}
        return {"success": True, "stack": "B", "text": text}
    
    return {"success": False, "error": error or "Beide Stacks fehlgeschlagen"}

if __name__ == "__main__":
    test_file = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/.jack_hey.m4a")
    if os.path.exists(test_file):
        print("--- START ROUTER TEST ---")
        result = asyncio.run(route_voice(test_file))
        print(f"--- ERGEBNIS: {result} ---")
    else:
        print(f"[ROUTER] Keine Testdatei: {test_file}")
