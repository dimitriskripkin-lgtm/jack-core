#!/usr/bin/env python3
"""Bruecke zu Claude Code (headless) auf dem Geraet.
Read-only Berater, der die ganze JACK-Umgebung kennt (liest ~/jack + CLAUDE.md).
Laeuft ueber Dimas claude.ai-Abo - kein API-Geld pro Aufruf."""
import os, subprocess
JACKDIR=os.path.expanduser("~/jack")

def _bin():
    pfx=os.environ.get("PREFIX","/data/data/com.termux/files/usr")
    return f"{pfx}/lib/node_modules/@anthropic-ai/claude-code-linux-arm64/claude"

def ask_claude(prompt, weiter=True, timeout=160):
    cmd=["grun", _bin(), "-p",
         "--allowedTools", "Read,Grep,Glob", "--max-turns", "15",
         "--append-system-prompt",
         "Antworte im Headless-Modus DIREKT und knapp auf die Frage. Kein Gruss, keine Rueckfrage, keine Git-Status-Kommentare. Deutsch, Kumpel-Ton."]
    if weiter: cmd.append("--continue")
    try:
        r=subprocess.run(cmd, cwd=JACKDIR, input=prompt, capture_output=True, text=True, timeout=timeout)
        out=(r.stdout or "").strip()
        if not out and weiter:
            return ask_claude(prompt, weiter=False, timeout=timeout)
        if not out:
            return (r.stderr or "keine Antwort")[:600]
        return out
    except subprocess.TimeoutExpired:
        return "Claude Code hat zu lange gebraucht (Timeout)."
    except Exception as e:
        return f"Claude-Bruecke Fehler: {e}"

if __name__=="__main__":
    import sys
    q=" ".join(sys.argv[1:]) or "Nenne kurz 3 JACK-Module und was sie tun."
    print(ask_claude(q, weiter=False))
