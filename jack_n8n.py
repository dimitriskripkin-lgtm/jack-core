"""JACK_TUNE_N8N (27.10.2026, Kap 307; Entwurf ChatGPT N1, Abnahme Claude).
HONOR -> XIAOMI -> n8n (nur 127.0.0.1 auf dem Xiaomi). Kein IO beim Import.
Schreibende Aufrufe brauchen confirmed=True (Dimas Knopf). Kein automatischer Retry.
Geheimnis nur per stdin, nie als Argument oder in Logs. Einmal-Marker pro request_id auf dem Xiaomi.
Claude-Aenderungen: Timeouts 20/30 s (Google-Aufruf in proot braucht laenger), Marker-Zeilenumbruch korrigiert.
"""
import json, re, shlex
from pathlib import Path

SECRET_FILE = Path("/data/data/com.termux/files/home/jack/.n8n_webhook_secret")
_ALLOWED = {"kalender"}
_REMOTE = """import json,sys,urllib.request,urllib.error,os,re
try:
 x=json.load(sys.stdin)
 rid=(x.get('payload') or {}).get('request_id')
 if not isinstance(rid,str) or not re.fullmatch(r'[a-fA-F0-9-]{16,64}',rid):
  raise ValueError('invalid_request_id')
 base=os.path.expanduser('~/.local/share/jack_n8n/once')
 os.makedirs(base,mode=0o700,exist_ok=True)
 marker=os.path.join(base,rid)
 try:
  fd=os.open(marker,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 except FileExistsError:
  print(json.dumps({'error':'duplicate_request_must_reconcile'}));sys.exit(0)
 with os.fdopen(fd,'w') as file:file.write('pending\\n')
 req=urllib.request.Request('http://127.0.0.1:5678/webhook/jack-'+x['name'],data=json.dumps(x['payload'],ensure_ascii=False).encode(),headers={'Content-Type':'application/json','X-JACK-Secret':x['secret']},method='POST')
 with urllib.request.urlopen(req,timeout=20) as response:
  raw=response.read(262144);result=json.loads(raw) if raw else {}
 if response.status==200 and result.get('ok') is True and result.get('event_id'):
  with open(marker,'w') as file:file.write('event_id='+str(result['event_id'])[:100]+'\\n')
 print(json.dumps({'http_status':response.status,'data':result}))
except urllib.error.HTTPError as e:
 print(json.dumps({'http_status':e.code,'error':'webhook_http_error'}))
except Exception as e:
 print(json.dumps({'error':type(e).__name__}))
"""


def _secret():
    st = SECRET_FILE.stat()
    if st.st_mode & 0o077:
        raise PermissionError("Secret-Datei muss chmod 600 haben")
    text = SECRET_FILE.read_text(encoding="utf-8").strip()
    if len(text) < 32 or len(text) > 256 or "\n" in text:
        raise ValueError("Webhook-Secret ungueltig")
    return text


def webhook(name, payload, *, confirmed=False):
    if name not in _ALLOWED:
        raise ValueError("Unbekannter Webhook")
    if not confirmed:
        raise PermissionError("Dimas ausdrueckliche Freigabe fehlt")
    if not isinstance(payload, dict):
        raise ValueError("Payload ist kein JSON-Objekt")
    rid = payload.get("request_id")
    if not isinstance(rid, str) or not re.fullmatch(r"[a-fA-F0-9-]{16,64}", rid):
        raise ValueError("request_id fehlt oder ungueltig")
    raw = json.dumps(payload, ensure_ascii=False, allow_nan=False)
    if len(raw.encode("utf-8")) > 8192:
        raise ValueError("Payload zu gross")
    data = json.dumps({"name": name, "payload": payload, "secret": _secret()}, ensure_ascii=False)
    try:
        import jack_xiaomi
        command = "python3 -c " + shlex.quote(_REMOTE)
        result = jack_xiaomi.run_shell(command, as_root=False, timeout=30, input_data=data)
    except Exception:
        return {"ok": False, "reason": "xiaomi_offline_or_bridge_error"}
    if not result.get("success"):
        return {"ok": False, "reason": "xiaomi_connection_failed"}
    try:
        obj = json.loads((result.get("stdout") or "")[:262144])
        ack = obj.get("data") or {}
        if obj.get("http_status") == 200 and ack.get("ok") is True and ack.get("event_id"):
            return {"ok": True, "event_id": str(ack["event_id"])}
        return {"ok": False, "reason": obj.get("error") or "not_confirmed_by_calendar",
                "http_status": obj.get("http_status")}
    except (ValueError, TypeError, AttributeError):
        return {"ok": False, "reason": "invalid_webhook_response"}
