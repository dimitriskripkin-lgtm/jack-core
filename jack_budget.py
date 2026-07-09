#!/usr/bin/env python3
"""Kosten-Bremse: Tageslimits fuer Gemini Text + Vision (Bilder teurer)."""
import os, json, datetime
F=os.path.expanduser("~/jack/.api_budget")
LIMITS={"text":300,"vision":40}

def _load():
    heute=str(datetime.date.today())
    try:
        d=json.load(open(F))
        if d.get("datum")!=heute: d={"datum":heute,"text":0,"vision":0}
    except Exception:
        d={"datum":heute,"text":0,"vision":0}
    return d

def check_and_count(kind="text"):
    d=_load()
    if d.get(kind,0)>=LIMITS.get(kind,300):
        return False, f"Tageslimit {kind} erreicht ({LIMITS[kind]}/Tag). Morgen wieder."
    d[kind]=d.get(kind,0)+1
    try: json.dump(d,open(F,"w"))
    except Exception: pass
    return True, f"{kind} {d[kind]}/{LIMITS[kind]}"

def add_tokens(n):
    d=_load(); d["tokens"]=d.get("tokens",0)+int(n or 0)
    try: json.dump(d,open(F,"w"))
    except Exception: pass

def status():
    d=_load()
    return f"Heute: Text {d.get('text',0)}/{LIMITS['text']} | Vision {d.get('vision',0)}/{LIMITS['vision']} | Tokens {d.get('tokens',0)}"
