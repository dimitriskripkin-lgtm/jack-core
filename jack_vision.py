#!/usr/bin/env python3
import os
import subprocess
import base64
from PIL import Image
import google.generativeai as genai
import jack_config

def get_screen_b64():
    path_png = os.path.expanduser('~/jack/vision_tmp.png')
    path_jpg = os.path.expanduser('~/jack/vision_tmp.jpg')
    
    cmd = "ssh -p 8022 xiaomi-jack 'su -c screencap -p' > " + path_png
    subprocess.run(cmd, shell=True, check=True)
    
    img = Image.open(path_png).convert('RGB')
    img.thumbnail((800, 800))
    img.save(path_jpg, 'JPEG', quality=65)
    
    with open(path_jpg, "rb") as f:
        b64_data = base64.b64encode(f.read()).decode('utf-8')
        
    os.remove(path_png)
    os.remove(path_jpg)
    
    return b64_data

def analyze_screen(prompt="Beschreibe kurz und präzise, was du auf diesem Bildschirm siehst. Welche App ist offen und welche Buttons gibt es?"):
    try:
        api_key = jack_config.get_param('API', 'gemini_key')
    except Exception:
        api_key = ''
        
    if not api_key:
        return "FEHLER: Kein Gemini API Key in der config.ini gefunden."
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    print("-> Ziehe Screenshot vom Xiaomi und komprimiere...")
    try:
        b64_data = get_screen_b64()
    except Exception as e:
        return f"FEHLER beim Screenshot-Stream: {e}"
    
    image_part = {
        'mime_type': 'image/jpeg',
        'data': b64_data
    }
    
    print("-> Sende Bild an Gemini Vision...")
    try:
        response = model.generate_content([prompt, image_part])
        return response.text
    except Exception as e:
        return f"FEHLER bei der Gemini API: {e}"

if __name__ == "__main__":
    result = analyze_screen()
    print("\n=== GEMINI VISION OUTPUT ===")
    print(result)
