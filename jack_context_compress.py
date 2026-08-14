#!/usr/bin/env python3
"""JACK Kontext-Kompression: FTS5 Pre-Filter vor Gemini. Nur Top-3 relevante Fakten senden."""
import os,sqlite3,json

DB=os.path.expanduser("~/jack/jack_memory.db")
MAX_FACTS=5
MAX_CHARS=300

def compress(prompt,full_mem_ctx):
    """Filtert mem_ctx auf prompt-relevante Eintraege via FTS5."""
    try:
        c=sqlite3.connect(DB)
        c.execute("PRAGMA journal_mode=WAL")
        # FTS5 Suche mit den wichtigsten Woertern aus dem Prompt
        words=[w for w in prompt.lower().split() if len(w)>3][:6]
        if not words: return full_mem_ctx
        query=" OR ".join(words)
        rows=c.execute(
            "SELECT cmd,result FROM memory_fts WHERE memory_fts MATCH ? LIMIT ?",
            (query,MAX_FACTS)).fetchall()
        c.close()
        if not rows: return full_mem_ctx
        compressed=chr(10).join(
            f"- {r[0][:60]}: {r[1][:MAX_CHARS]}" for r in rows
        )
        return compressed
    except Exception:
        return full_mem_ctx

def estimate_tokens(text):
    """Grobe Token-Schaetzung: 4 Zeichen ~ 1 Token."""
    return len(text)//4

if __name__=="__main__":
    test="Wie ist der RAM-Status auf dem Honor?"
    fake_ctx="dummy kontext fuer test"
    print("Komprimiert:",compress(test,fake_ctx))
