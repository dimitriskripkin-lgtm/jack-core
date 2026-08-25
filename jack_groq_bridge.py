#!/usr/bin/env python3
import os,json,urllib.request

MODEL="openai/gpt-oss-120b"
API_URL="https://api.groq.com/openai/v1/chat/completions"
UA="Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36"

def load_key():
    try:
        for l in open(os.path.expanduser("~/.jack_secrets")):
            if "GROQ_API_KEY" in l and "=" in l:
                return l.split("=",1)[1].strip().strip(chr(34)).strip(chr(39))
    except Exception: pass
    return os.environ.get("GROQ_API_KEY","")

def ask_groq(system_prompt, user_msg, timeout=20):
    key=load_key()
    if not key: return "[Groq] Kein API-Key"
    payload=json.dumps({"model":MODEL,"messages":[{"role":"system","content":system_prompt},{"role":"user","content":user_msg}],"max_tokens":1024,"temperature":0.55}).encode()
    req=urllib.request.Request(API_URL,data=payload,headers={"Content-Type":"application/json","Authorization":"Bearer "+key,"User-Agent":UA})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[Groq Fehler] {e}"

if __name__=="__main__":
    persona=open(os.path.expanduser("~/jack/jack_persona.md"),encoding="utf-8").read()
    print(ask_groq(persona,"Wer bin ich und was haben wir heute gebaut?"))
