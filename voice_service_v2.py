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
 try:
  for f in(TMP_M4A,TMP_WAV):
   os.path.exists(f) and os.remove(f)
  trigger = os.path.expanduser("~/.voice_trigger")
  done = os.path.expanduser("~/.voice_done")
  if os.path.exists(done): os.remove(done)
  open(trigger, "w").write(str(sec))
  deadline = sec + 10
  waited = 0
  while waited < deadline:
    if os.path.exists(done): break
    import time; time.sleep(1); waited += 1
 except Exception as e:state["last_error"]=str(e)
 finally:
  state["recording"]=False
  if os.path.exists(TMP_M4A) and os.path.getsize(TMP_M4A)>1000:threading.Thread(target=transcribe_async,daemon=True).start()
  else:state["last_error"]="Keine Aufnahme";state["ready"]=True
def transcribe_async():
 state["transcribing"]=True
 try:
  subprocess.run(["ffmpeg","-y","-i",TMP_M4A,"-ar","16000","-ac","1","-c:a","pcm_s16le",TMP_WAV],timeout=30,capture_output=True,check=True)
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
