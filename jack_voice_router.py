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
    print("[ROUTER] Stack B: Fallback auf Offline Whisper + Ollama...")
    try:
        import jack_voice_processor as vp
        base_name = os.path.splitext(audio_path)[0]
        wav_path = base_name + ".wav"
            
        subprocess.run(["ffmpeg", "-y", "-i", audio_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", wav_path], capture_output=True, check=True)
        
        text, _, error = vp.process_voice_message(wav_path)
        if text:
            print(f"[ROUTER] Stack B ERFOLGREICH: Whisper erkannte: '{text}'")
            return text, None
        else:
            print(f"[ROUTER] Stack B FEHLER: {error}")
            return None, error
    except Exception as e:
        print(f"[ROUTER] Stack B FEHLER: {type(e).__name__} - {str(e)[:100]}")
        return None, str(e)

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
        
    text, error = await process_stack_b_offline(audio_path)
    if text:
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
