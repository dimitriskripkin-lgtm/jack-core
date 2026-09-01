#!/usr/bin/env python3
"""jack_talk_trainer.py — Automatischer JACK-Lehrer. Liest Samples, fragt Gemini, härtet Persona."""
MODULE_VERSION = 1

import os, sys, json, time
J = os.path.expanduser("~/jack")
sys.path.insert(0, J)

SAMPLES = os.path.join(J, "missions", "talk_samples.jsonl")
PERSONA = os.path.join(J, "jack_persona.md")
LOG = os.path.join(J, "trainer.log")
MAX_BREACHES_PER_RUN = 3  # Gemini-Budget schonen

def _log(msg):
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(LOG, "a") as f:
        f.write(f"{ts} {msg}\n")
    print(msg)

def get_breaches(n=100):
    """Liest letzte n Samples, gibt Breach-Liste zurück."""
    if not os.path.exists(SAMPLES): return []
    import jack_talk_contract as tc
    lines = open(SAMPLES, errors="ignore").read().splitlines()
    breaches = []
    for line in lines[-n:]:
        try:
            d = json.loads(line)
            u = d.get("u",""); j = d.get("j","")
            hits = tc.score(j, u)
            if hits:
                breaches.append({"u": u, "j": j, "hits": hits})
        except Exception:
            pass
    return breaches

def ask_gemini_for_better(u, j, hits):
    """Fragt Gemini: Was wäre eine bessere Antwort?"""
    try:
        import jack_gemini_bridge as gb
        prompt = f"""Du bist ein JACK-Trainer. JACK ist ein KI-System auf Android, Kumpel von Dima, kein Assistent.

JACK hat auf diese Nachricht geantwortet:
USER: {u[:100]}
JACK: {j[:200]}

Das war ein Verstoß gegen diese Regeln: {hits}

Regeln für JACK:
- Kein "Klar, Dima." als Opener
- Keine Pflichtfragen ("schwebt dir vor", "was genau willst du")
- Nachtschicht/LKW nicht selbst erwähnen
- Kurz, direkt, 1-3 Sätze
- Ich-Form, kein Dritte-Person über JACK

Gib NUR eine bessere Antwort in 1-2 Sätzen. Keine Erklärung, kein Präambel."""
        return gb.ask_gemini(prompt)
    except Exception as e:
        return None

def update_persona(bad_example, good_example, hits):
    """Fügt SCHLECHT/GUT Beispiel in persona.md ein."""
    content = open(PERSONA, errors="ignore").read()
    marker = "FAKTFRAGEN"
    if marker not in content:
        return False
    insert = f"""
GELERNT (auto {time.strftime('%d.%m.%Y')}) — Verstoß: {hits}
SCHLECHT: "{bad_example[:80]}"
GUT: "{good_example[:80]}"
"""
    content = content.replace(marker, insert + marker)
    open(PERSONA, "w").write(content)
    return True

def run():
    _log("=== TRAINER START ===")
    breaches = get_breaches(100)
    if not breaches:
        _log("Keine Breaches gefunden — JACK ist sauber")
        return 0

    _log(f"{len(breaches)} Breaches gefunden")
    trained = 0

    for b in breaches[:MAX_BREACHES_PER_RUN]:
        _log(f"Breach: {b['hits']} | {b['u'][:40]} → {b['j'][:60]}")
        better = ask_gemini_for_better(b["u"], b["j"], b["hits"])
        if not better:
            _log("Gemini: kein Output — skip")
            continue
        better = better.strip()[:120]
        _log(f"Gemini-Vorschlag: {better}")
        if update_persona(b["j"], better, b["hits"]):
            _log(f"Persona aktualisiert ✅")
            trained += 1
        time.sleep(2)  # Rate-Limit schonen

    _log(f"=== TRAINER ENDE: {trained} Verbesserungen ===")
    return trained

if __name__ == "__main__":
    n = run()
    sys.exit(0 if n >= 0 else 1)
