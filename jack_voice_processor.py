import os
import subprocess
from elevenlabs.client import ElevenLabs

WHISPER_PATH = os.path.expanduser("~/whisper.cpp/build/bin/whisper-cli")
MODEL_PATH = os.path.expanduser("~/whisper.cpp/models/ggml-base.bin")
SECRETS = os.path.expanduser("~/.jack_secrets")

def get_secret(key):
    with open(SECRETS, "r") as f:
        for line in f:
            if key in line and "=" in line:
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None

def process_voice_message(ogg_path):
    wav_path = ogg_path.replace(".ogg", ".wav")
    
    # Audio konvertieren
    subprocess.run(["ffmpeg", "-y", "-i", ogg_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", wav_path], check=True, capture_output=True)
    
    # Audio transkribieren mit 6 CPU-Threads für maximale Geschwindigkeit
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
    except Exception:
        pass

    return resp_wav, text, response_text
