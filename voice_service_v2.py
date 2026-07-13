import os,subprocess,threading,logging
from flask import Flask,jsonify
HOME=os.path.expanduser("~")
WHISPER=HOME+"/whisper.cpp/build/bin/whisper-cli"
MODEL=HOME+"/whisper.cpp/models/ggml-base.bin"
TMP_M4A=HOME+"/.voice_rec.m4a"
TMP_WAV=HOME+"/.voice_rec.wav"
PORT=5001
logging.basicConfig(level=logging.INFO)
app=Flask(__name__)
state={"recording":False,"transcribing":False,"last_text":"","last_error":"","ready":True}
def record_async(sec=8):
 state["recording"]=True;state["ready"]=False
 done = os.path.expanduser("~/.voice_done")
 trigger = os.path.expanduser("~/.voice_trigger")
 try:
  if os.path.exists(done): os.remove(done)
  if os.path.exists(TMP_WAV): os.remove(TMP_WAV)
  import os as _os; _os.path.exists(done) and _os.remove(done)
  open(trigger, "w").write(str(sec))
  import time as _t; waited = 0
  while waited < sec + 12:
   if os.path.exists(done):
    import time as _t2
    _t2.sleep(3)
    prev=0
    for _ in range(5):
     cur=os.path.getsize(TMP_M4A) if os.path.exists(TMP_M4A) else 0
     if cur==prev and cur>1000: break
     prev=cur; _t2.sleep(1)
    break
   _t.sleep(1); waited += 1
 except Exception as e: state["last_error"]=str(e)
 finally:
  state["recording"]=False
  done = os.path.expanduser("~/.voice_done")
  import time as _t
  waited2 = 0
  while waited2 < 5:
    if os.path.exists(TMP_M4A) and os.path.getsize(TMP_M4A)>1000: break
    _t.sleep(0.5); waited2 += 0.5
  if os.path.exists(TMP_M4A) and os.path.getsize(TMP_M4A)>1000:threading.Thread(target=transcribe_async,daemon=True).start()
  else:state["last_error"]="Keine Aufnahme";state["ready"]=True
def transcribe_async():
 state["transcribing"]=True
 try:
  import os as _o; _o.path.exists(TMP_WAV) and _o.remove(TMP_WAV)
  subprocess.run(["ffmpeg","-y","-i",TMP_M4A,"-ar","16000","-ac","1",TMP_WAV],timeout=30,capture_output=True,check=True)
  res=subprocess.run([WHISPER,"-m",MODEL,"-f",TMP_WAV,"-l","de","-nt","-np"],timeout=60,capture_output=True,text=True)
  state["last_text"]=res.stdout.strip()
  if not state["last_text"]:state["last_error"]="Leeres Transkript"
 except Exception as e:state["last_error"]=str(e)
 finally:state["transcribing"]=False;state["ready"]=True
@app.route("/record/<int:s>")
def rec(s=8):
 if not state["ready"]:return jsonify({"error":"busy"})
 threading.Thread(target=record_async,args=(min(s,30),),daemon=True).start()
 return jsonify({"status":"ok","seconds":s})
@app.route("/status")
def sts():return jsonify(state)
@app.route("/last")
def lst():return jsonify({"text":state["last_text"],"error":state["last_error"]})
if __name__=="__main__":app.run(host="0.0.0.0",port=PORT,threaded=True)
