#!/usr/bin/env python3
"""Sichere SEARCH/REPLACE-Patches. Nie ganze Dateien ueberschreiben."""
import os, re, shutil, subprocess, time

MARK_S = "<<<<<<< SEARCH"
MARK_M = "======="
MARK_R = ">>>>>>> REPLACE"

def parse_blocks(text):
    """Zerlegt Gemini-Antwort in [(search, replace), ...]"""
    blocks = []
    pat = re.compile(
        re.escape(MARK_S) + r"\n(.*?)\n" + re.escape(MARK_M) + r"\n(.*?)\n?" + re.escape(MARK_R),
        re.DOTALL)
    for m in pat.finditer(text):
        blocks.append((m.group(1), m.group(2)))
    return blocks

def apply_blocks(original, blocks):
    """Wendet Bloecke an. Fehler wenn Suchtext fehlt oder mehrdeutig."""
    out = original
    for search, replace in blocks:
        if not search.strip():
            return None, "Leerer SEARCH-Block"
        cnt = out.count(search)
        if cnt == 0:
            return None, f"SEARCH-Text nicht gefunden: {search[:60]!r}"
        if cnt > 1:
            return None, f"SEARCH-Text mehrdeutig ({cnt}x): {search[:60]!r}"
        out = out.replace(search, replace, 1)
    return out, "OK"

def verify(original, patched, file_path):
    """Groessenwaechter + echter Syntax-Check der GANZEN Datei."""
    if not patched.strip():
        return False, "Ergebnis ist leer"
    if len(patched) < len(original) * 0.5:
        return False, f"Datei schrumpft zu stark ({len(original)}->{len(patched)}) - Abbruch"
    tmp_dir = os.environ.get("TMPDIR", os.path.expanduser("~/jack"))
    tmp = os.path.join(tmp_dir, f"patchcheck_{int(time.time())}.py")
    try:
        with open(tmp, "w") as f:
            f.write(patched)
        r = subprocess.run(["python3", "-m", "py_compile", tmp],
                           capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            return False, f"SyntaxError: {r.stderr.strip()[:200]}"
        return True, "OK"
    except Exception as e:
        return False, str(e)
    finally:
        for f in (tmp, tmp + "c"):
            if os.path.exists(f):
                os.remove(f)

def safe_patch(file_path, gemini_answer, backup_dir=None):
    """Kompletter sicherer Ablauf. Gibt (ok, meldung, diff_preview)."""
    if not os.path.exists(file_path):
        return False, f"Datei fehlt: {file_path}", ""
    original = open(file_path).read()
    blocks = parse_blocks(gemini_answer)
    if not blocks:
        return False, "Keine gueltigen SEARCH/REPLACE-Bloecke", ""
    patched, msg = apply_blocks(original, blocks)
    if patched is None:
        return False, msg, ""
    ok, why = verify(original, patched, file_path)
    if not ok:
        return False, why, ""
    preview = "\n".join(f"- {s[:70]}\n+ {r[:70]}" for s, r in blocks)
    bdir = backup_dir or os.path.expanduser("~/jack_backups")
    os.makedirs(bdir, exist_ok=True)
    bpath = os.path.join(bdir, f"{os.path.basename(file_path)}.bak_{int(time.time())}")
    shutil.copy2(file_path, bpath)
    with open(file_path, "w") as f:
        f.write(patched)
    return True, f"Gepatcht ({len(blocks)} Block/Bloecke). Backup: {bpath}", preview
