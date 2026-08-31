#!/usr/bin/env python3
MODULE_VERSION = 1
# JACK_TUNE_VOICEH
import os, json, urllib.request, subprocess, threading
J="/data/data/com.termux/files/home/jack"
def get_voice(api, token, file_id, out_path):
    url=api+"/getFile?file_id="+file_id
    with urllib.request.urlopen(url) as res:
        path=json.loads(res.read())["result"]["file_path"]
    urllib.request.urlretrieve("https://api.telegram.org/file/bot"+token+"/"+path, out_path)
def send_voice(api, chat_id, file_path):
    if not file_path: return
    subprocess.run(["curl","-s","-X","POST",api+"/sendVoice","-F","chat_id="+str(chat_id),"-F","voice=@"+file_path],timeout=30)
def handle_voice(msg, ctx):
    file_id=msg["voice"]["file_id"]
    ogg=os.path.join(J,"voice_"+file_id+".ogg")
    send=ctx["send"]; kb=ctx["send_keyboard"]; pend=ctx["pending"]
    try: ctx.get("vibrate", lambda *a,**k: None)(60)
    except Exception: pass
    send("\U0001f3a4")
    def _vrun():
        try:
            get_voice(ctx["api"], ctx["token"], file_id, ogg)
            from jack_voice_processor import process_voice_message
            rw2, heard, ans = process_voice_message(ogg)
            ans=str(ans or "")
            if ans.startswith("__APPCMD__:"):
                pkg=ans.split(":",1)[1]
                cmd='ssh xiaomi-jack "su -c \'monkey -p '+pkg+' -c android.intent.category.LAUNCHER 1\'"'
                pend.clear(); pend["cmd"]=cmd
                kb("VORSCHLAG:\n"+cmd, [[("Ausfuehren","run_exec"),("Abbrechen","cancel_exec")]])
                send("Du: "+str(heard)+"\n\nJACK: App-Befehl erkannt - Freigabe tippen.")
                return
            try:
                import jack_intent_lookup as il
                intent, cmd = il.suggest_deep_navigation(str(heard))
            except Exception:
                intent, cmd = None, None
            if cmd:
                pend.clear(); pend["cmd"]=cmd
                kb("VORSCHLAG (Deep):\n"+cmd, [[("Ausfuehren","run_exec"),("Abbrechen","cancel_exec")]])
                send("Du: "+str(heard)+"\n\nJACK: Deep-Navigation bereit - Freigabe tippen.")
                return
            try:
                import jack_intent_apps
                if jack_intent_apps.try_app_launch(str(heard), pend, kb):
                    send("Du: "+str(heard)+"\n\nJACK: App-Befehl bereit - Freigabe tippen.")
                    return
            except Exception:
                pass
            try:
                import jack_exec_parser
                ans = jack_exec_parser.parse_and_prepare(ans, pend, kb) or ans
            except Exception:
                pass
            send("Du: "+str(heard)+"\n\nJACK: "+str(ans))
            try: send_voice(ctx["api"], ctx["chat_id"], rw2)
            except Exception: pass
            for f in (ogg, rw2):
                try:
                    if f and os.path.isfile(f): os.remove(f)
                except Exception: pass
        except Exception as e:
            send("Sprachfehler: "+str(e)[:100])
    threading.Thread(target=_vrun, daemon=True).start()
