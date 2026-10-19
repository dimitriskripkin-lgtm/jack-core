import re

# JACK_TUNE_OBSLINE (19.10.2026, F12): vorher schlug jedes Wort wie "exception" irgendwo in stdout an,
# auch beim Lesen von Quellcode (cat/sed/grep). Jetzt: stderr wie bisher komplett, stdout nur Zeilenanfaenge,
# an denen echte Fehlermeldungen stehen (Python-Traceback, Exception-Zeile, bash, git fatal).
BAD_PATTERNS = [
    "command not found", "permission denied", "syntax error",
    "traceback", "fatal", "exception", "error:"
]
_LINE = re.compile(r"^(traceback \(most recent call last\)|\S+:[^\n]*: (?:command not found|permission denied)"
                   r"|fatal:|syntaxerror|[a-z_.]*error: |[a-z_.]*exception: |[a-z_.]*exception$)", re.M)

def check_output(stdout_str, stderr_str):
    err = str(stderr_str or "").lower()
    found = [p for p in BAD_PATTERNS if p in err]
    for m in _LINE.finditer(str(stdout_str or "").lower()):
        k = m.group(1)[:40]
        if k not in found:
            found.append(k)
    return len(found) == 0, found

if __name__ == "__main__":
    ok, errs = check_output("bash: foo: command not found", "")
    print(f"Observer Test: OK={ok}, Errs={errs}")
