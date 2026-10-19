#!/usr/bin/env python3
"""JACK Vision: Xiaomi-Screen -> Gemini 2.5 Flash via REST (kein genai-Paket).
get_screen_b64(max_px, quality): Screenshot via SSH, PIL-Kompression, Base64.
vision_ask(prompt, ...): Budget-Check -> Vision-Call -> Text zurueck."""
import os, subprocess, base64, json, urllib.request

def _gemini_key():
    for l in open(os.path.expanduser('~/.jack_secrets')):
        if 'GEMINI_API_KEY' in l:
            return l.split('"')[1] if '"' in l else l.split('=',1)[1].strip()
    return ''

def get_screen_b64(max_px=1080, quality=80):
    from PIL import Image
    png = os.path.expanduser('~/jack/vision_tmp.png')
    jpg = os.path.expanduser('~/jack/vision_tmp.jpg')
    subprocess.run("ssh -o ConnectTimeout=5 xiaomi-jack 'su -c screencap -p' > " + png,
                   shell=True, check=True, timeout=20)
    img = Image.open(png).convert('RGB')
    img.thumbnail((max_px, max_px * 3))
    img.save(jpg, 'JPEG', quality=quality)
    b64 = base64.b64encode(open(jpg, 'rb').read()).decode()
    for f in (png, jpg):
        try: os.remove(f)
        except OSError: pass
    return b64

def vision_ask(prompt, b64=None, max_px=1080, quality=80, timeout=45):
    import jack_budget
    ok, msg = jack_budget.check_and_count('vision')
    if not ok: return '[BUDGET] ' + msg
    key = _gemini_key()
    if not key: return '[FEHLER] Kein GEMINI_API_KEY in ~/.jack_secrets'
    if b64 is None:
        try: b64 = get_screen_b64(max_px, quality)
        except Exception as e: return '[FEHLER Screenshot] ' + str(e)[:120]
    _vm = 'gemini-2.5-flash'
    try:
        import jack_modelmap as _mm  # JACK_TUNE_MODELMAP (17.10.2026)
        _vm = _mm.aktuell(_vm)
    except Exception:
        pass
    url = ('https://generativelanguage.googleapis.com/v1beta/models/'
           + _vm + ':generateContent?key=' + key)
    payload = {"contents": [{"parts": [
        {"text": prompt},
        {"inline_data": {"mime_type": "image/jpeg", "data": b64}}]}],
        "generationConfig": {"maxOutputTokens": 2048, "temperature": 0.2, "thinkingConfig": {"thinkingBudget": 0}}}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            res = json.loads(r.read())
        try:
            import jack_budget as _b
            _um = res.get('usageMetadata', {})  # JACK_TUNE_VISIONEUR echte Kosten
            _pin = _um.get('promptTokenCount', 0); _pout = _um.get('candidatesTokenCount', 0) + _um.get('thoughtsTokenCount', 0)
            _b.add_tokens(_um.get('totalTokenCount', 0), _b.eur_fuer(res.get('modelVersion') or locals().get('_vm') or 'gemini-2.5-flash', _um))  # JACK_TUNE_PREISMODELL
        except Exception: pass
        return res['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        if getattr(e, 'code', None) == 404:
            try:
                import jack_modelmap as _mm  # JACK_TUNE_MODELMAP: naechster Aufruf nutzt den Ersatz
                _mm.melde_404(_vm)
            except Exception:
                pass
        return '[FEHLER Gemini] ' + str(e)[:150]

def analyze_screen(prompt="Beschreibe kurz was auf dem Screen ist. Welche App, welche Buttons?"):
    return vision_ask(prompt)

if __name__ == '__main__':
    import sys
    p = ' '.join(sys.argv[1:]) or None
    print(analyze_screen(p) if p else analyze_screen())
