# JACK_TUNE_SAFETEXT: Text fuer "input text" shell-sicher machen (Whitelist)
import re
_OK = re.compile(r"[^A-Za-z0-9 .,:;_@/+=!#()-]")
def typed(txt, maxlen=300):
    """Nur harmlose Zeichen behalten, Leerzeichen -> %s. Keine Quotes/$/`/;|&<>."""
    s = _OK.sub("", str(txt))[:maxlen]
    s = s.replace(";", "").replace("(", "").replace(")", "").replace("!", "").replace("#", "")
    return s.replace(" ", "%s")
