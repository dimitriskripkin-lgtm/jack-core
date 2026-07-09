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
    result = subprocess.run([WHISPER_PATH, "-m", MODEL_PATH, "-f", wav_path, "-nt", "-t", "6"], capture_output=True, text=True)
    text = result.stdout.strip()
    
    # Gemini antworten lassen
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
