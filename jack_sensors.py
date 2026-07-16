#!/usr/bin/env python3
"""JACK Sinne: Xiaomi-Sensoren via SSH + Gemini Vision (Augen)."""
import os, json, base64, subprocess, urllib.request

XIAOMI="10.244.147.131"; PORT="8022"; KEY=os.path.expanduser("~/.ssh/id_jack")

def _ssh(cmd, timeout=30):
    full=["ssh","-i",KEY,"-o","BatchMode=yes","-o","StrictHostKeyChecking=no",
          "-o","UserKnownHostsFile=/dev/null","-o","ConnectTimeout=6","-p",PORT,
          f"root@{XIAOMI}", cmd]
    try:
        r=subprocess.run(full,capture_output=True,text=True,timeout=timeout)
        return r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT"

def get_battery():
    out,err=_ssh("termux-battery-status",timeout=15)
    try:
        d=json.loads(out)
        return f"Akku {d.get('percentage')}%, {d.get('status')}, {d.get('temperature')}C"
    except Exception:
        return f"Akku unklar ({err or out[:60]})"

def get_motion():
    out,err=_ssh("timeout 8 termux-sensor -s linear_acceleration -n 1; termux-sensor -c >/dev/null 2>&1",timeout=18)
    try:
        d=json.loads(out); vals=list(d.values())[0].get("values",[])
        mag=sum(v*v for v in vals)**0.5
        return f"Bewegung {mag:.2f} ({'in Bewegung' if mag>0.6 else 'ruhig'})"
    except Exception:
        return f"Sensor unklar ({err or out[:60]})"

def get_location(timeout=50):
    out,err=_ssh("termux-location -p network 2>/dev/null || termux-location -p gps",timeout=timeout)
    try:
        return json.loads(out)
    except Exception:
        return {"error": err or out[:80] or "keine Position"}

def snap_photo(local_path=None):
    remote="/data/data/com.termux/files/home/.jack_snap.jpg"
    _ssh(f"termux-camera-photo -c 0 {remote}",timeout=25)
    out,err=_ssh(f"base64 {remote}",timeout=25)
    b64="".join(out.split()) if out else ""
    if not b64:
        return None, f"Kein Foto ({err})"
    if local_path:
        try: open(local_path,"wb").write(base64.b64decode(b64))
        except Exception as _e:
            import jack_log; jack_log.log_decision('SILENT-FAIL jack_sensors', str(_e)[:120])
    return b64, "OK"

def see(frage="Was ist auf dem Bild? Antworte kurz auf Deutsch."):
    import jack_budget
    _ok,_m=jack_budget.check_and_count("vision")
    if not _ok: return _m
    b64,msg=snap_photo()
    if not b64: return f"Kamera-Fehler: {msg}"
    import jack_gemini_bridge as gb
    key=gb.load_api_key()
    url=f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={key}"
    payload={"contents":[{"parts":[{"text":frage},{"inline_data":{"mime_type":"image/jpeg","data":b64}}]}]}
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=45) as res:
            r=json.loads(res.read())
            return r["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        return f"Vision-Fehler: {e}"
