# JACK_TUNE_PYFLAKES: nur lesen. pyflakes ueber alle Module, Bericht nach ARBEITSPLATZ/gemeinsam/pyflakes_lauf.md
import os, sys, glob, subprocess, time
J = os.environ.get("JACK_HB_HOME", os.path.expanduser("~/jack"))
OUT = J + "/ARBEITSPLATZ/gemeinsam/pyflakes_lauf.md"
SCHWER = ("undefined name", "referenced before assignment", "unable to detect undefined names", "redefinition of unused", "syntax", "invalid syntax")

def run():
    t0 = time.time()
    files = sorted(glob.glob(J + "/*.py"))
    try:
        subprocess.run([sys.executable, "-m", "pyflakes", "--version"], capture_output=True, timeout=20, check=True)
    except Exception:
        open(OUT, "w").write("# Pruefstand\nFEHLER: pyflakes nicht installiert. HONOR: pip install pyflakes\n")
        return
    schwer, leicht, n = [], 0, 0
    for f in files:
        n += 1
        try:
            r = subprocess.run([sys.executable, "-m", "pyflakes", f], capture_output=True, text=True, timeout=60)
        except Exception as e:
            schwer.append("%s: pyflakes-Abbruch %s" % (os.path.basename(f), type(e).__name__)); continue
        for l in (r.stdout + r.stderr).splitlines():
            l = l.replace(J + "/", "")
            if any(k in l for k in SCHWER): schwer.append(l)
            else: leicht += 1
    txt = "# pyflakes-Lauf\nDateien: %d, schwere Funde: %d, leichte (unused import/variable usw.): %d, Dauer %.0fs\n\n## Schwer\n" % (n, len(schwer), leicht, time.time() - t0)
    txt += "\n".join("- " + s for s in schwer[:300]) + "\n"
    open(OUT, "w").write(txt)

if __name__ == "__main__":
    run()
    print(open(OUT).read()[:1500])
