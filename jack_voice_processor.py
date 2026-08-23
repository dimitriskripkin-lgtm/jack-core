import os
try:
    import jack_logging as _jlog
except Exception:
    _jlog = None
import subprocess
import jack_guard
WHISPER_PATH = os.path.expanduser("~/whisper.cpp/build/bin/whisper-cli")
MODEL_PATH = os.path.expanduser("~/whisper.cpp/models/ggml-small.bin")
SECRETS = os.path.expanduser("~/.jack_secrets")

def get_secret(key):
    with open(SECRETS, "r") as f:
        for line in f:
            if key in line and "=" in line:
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None

def process_voice_message(ogg_path):
    wav_path = ogg_path.replace(".ogg", ".wav")
    resp_wav = ogg_path.replace(".ogg", "_resp.wav")
    try:
        subprocess.run(["ffmpeg","-y","-i",ogg_path,"-ar","16000","-ac","1","-c:a","pcm_s16le",wav_path], check=True, capture_output=True)
    except Exception as e:
        return None, "", f"ffmpeg-Fehler: {e}"
    # P8 (Qwen 22.08.): Whisper auf Xiaomi wenn Honor heiss, Fallback lokal
    import jack_heat_protection as _hp
    try:
        if _hp.worker_target() == "xiaomi":
            try:
                # P10 (Qwen 22.08.): SSH-PIPE statt scp (schneller, kein Temp-File)
                # Audio via stdin an Xiaomi streamen, dort direkt verarbeiten
                with open(wav_path, 'rb') as f:
                    result = subprocess.run(
                        ["ssh", "xiaomi-jack", 
                         "~/whisper.cpp/build/bin/whisper-cli -m ~/whisper.cpp/models/ggml-small.bin -f - -l de -nt -t 4"],
                        stdin=f, capture_output=True, text=True, timeout=30
                    )
                text = " ".join(result.stdout.split()).strip()
                if not text:
                    raise ValueError("Leeres Ergebnis von Xiaomi")
                print(f"P8: Whisper auf Xiaomi OK")
            except Exception as e:
                print(f"P8: Xiaomi-Whisper Fehler ({e}), Fallback lokal")
                with jack_guard.Guard("whisper"):
                    result = subprocess.run([WHISPER_PATH,"-m",MODEL_PATH,"-f",wav_path,"-l","de","-nt","-t","6"], capture_output=True, text=True)
                text = " ".join(result.stdout.split()).strip()
        else:
            # Honor kuehl - lokale Ausfuehrung
            with jack_guard.Guard("whisper"):
                result = subprocess.run([WHISPER_PATH,"-m",MODEL_PATH,"-f",wav_path,"-l","de","-nt","-t","6"], capture_output=True, text=True)
            text = " ".join(result.stdout.split()).strip()
    except Exception as e:
        return None, "", f"Whisper-Fehler: {e}"
    if not text:
        return None, "", "Nichts verstanden - nochmal?"
    # UI-Intents vor Chat-LLM (Hauptleitung jack_exec)
    try:
        import jack_exec
        _ui = jack_exec.handle_ui_intent(text)
        if _ui:
            return None, text, _ui
    except Exception as _uie:
        pass
    try:
        if text.lower().strip().startswith("claude"):
            import jack_claude
            response_text = jack_claude.ask_claude(text)
        else:
            from jack_talk import talk_to_gemini
            response_text = talk_to_gemini(text)
    except Exception as e:
        return None, text, f"Denk-Fehler: {e}"
    try:
        from elevenlabs.client import ElevenLabs
        client = ElevenLabs(api_key=get_secret("ELEVENLABS_API_KEY"))
        audio = client.text_to_speech.convert(text=response_text, voice_id=get_secret("ELEVENLABS_VOICE_ID"), model_id="eleven_flash_v2_5")
        with open(resp_wav,"wb") as f:
            for chunk in audio: f.write(chunk)
    except Exception as e:
        import subprocess as _sp, jack_log
        jack_log.log_decision("TTS-FALLBACK","ElevenLabs fehlgeschlagen, nutze espeak: "+str(e)[:80])
        try:
            _sp.run(["espeak-ng","-v","de","-s","140","-w",resp_wav,response_text[:500]],timeout=15,capture_output=True,check=True)
        except Exception as e2:
            return None, text, f"TTS-Fehler (EL+espeak): {e2}"
    try:
        os.remove(wav_path)
    except Exception as _le:
        _jlog and _jlog.fehler("jack_voice_processor","unbenannt",_le)
    return resp_wav, text, response_text
def _DEAD_ORIGINAL_process_voice_message(ogg_path):
    wav_path = ogg_path.replace(".ogg", ".wav")
    
    # Audio konvertieren
    subprocess.run(["ffmpeg", "-y", "-i", ogg_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", wav_path], check=True, capture_output=True)
    
    # Audio transkribieren mit 6 CPU-Threads für maximale Geschwindigkeit
    with jack_guard.Guard("whisper"):
        result = subprocess.run([WHISPER_PATH, "-m", MODEL_PATH, "-f", wav_path, "-l", "de", "-nt", "-t", "6"], capture_output=True, text=True)
    text = " ".join(result.stdout.split()).strip()
    
    # Intent-Routing: direkte Befehle ohne Gemini-Umweg
    tlow = text.lower()
    sys.path.insert(0, os.path.expanduser("~/jack"))
    from kortex_memory import add_memory, search_memory

    if "merke" in tlow:
        idx = tlow.find("merke")
        inhalt = text[idx+5:].strip(" ,.:-")
        if inhalt:
            r = add_memory(inhalt, category="voice", source="voice", tags="")
            response_text = f"Gemerkt: {inhalt[:100]}"
        else:
            response_text = "Ich habe nichts zum Merken verstanden."
    elif "such" in tlow:
        idx = tlow.find("such")
        q = text[idx+4:].strip(" ,.:-")
        q = q[1:].strip() if q[:1] == "e" else q
        results = search_memory(q, limit=3) if q else None
        if not results or isinstance(results, dict):
            response_text = f"Nichts gefunden fuer {q}." if q else "Wonach soll ich suchen?"
        else:
            teile = [r["content"][:80] for r in results]
            response_text = "Gefunden: " + " | ".join(teile)
    elif tlow.strip().startswith("claude"):
        import jack_claude
        response_text = jack_claude.ask_claude(text)
    else:
        from jack_talk import talk_to_gemini
        response_text = talk_to_gemini(text)
    
    # Antwort als Sprache generieren (Modern SDK Syntax)
    from elevenlabs.client import ElevenLabs
    client = ElevenLabs(api_key=get_secret("ELEVENLABS_API_KEY"))
    audio = client.text_to_speech.convert(
        text=response_text,
        voice_id=get_secret("ELEVENLABS_VOICE_ID"),
        model_id="eleven_flash_v2_5"
    )
    
    resp_wav = ogg_path.replace(".ogg", "_resp.wav")
    with open(resp_wav, "wb") as f:
        for chunk in audio:
            f.write(chunk)
            
    try:
        os.remove(wav_path)
    except Exception as _le:
        _jlog and _jlog.fehler("jack_voice_processor","unbenannt",_le)

    return resp_wav, text, response_text
