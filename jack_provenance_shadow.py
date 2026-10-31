"""W4 Schatten-Provenance, NUR ENTWURF. Keine IO beim Import.
Kein Ausfuehrungs-Gate: attach()/check() erzeugen ausschließlich Metadaten/Code,
shadow_check_path() loggt nur und darf NIE den Runner stoppen.
"""
import hashlib, hmac, json, os, re, secrets, stat, time

ROOT = "/data/data/com.termux/files/home/jack"
KEY = os.path.expanduser("~/.jack_provenance_shadow.key")  # ausserhalb des JACK-Repos
LOG = os.path.join(ROOT, "logs", "provenance_shadow.jsonl")
PREFIX = b"JACK-PROVENANCE-SHADOW-V1\0"
KID = "shadow-20261029"
FIXED = {"v": 1, "issuer": "jack-mcp", "aud": "jack-mission-runner",
         "alg": "HMAC-SHA256", "kid": KID, "channel": "mcp"}
ROLES = {"claude", "legacy", "chatgpt", "grok", "gemini", "nachtlauf"}
HEX32 = re.compile(r"[a-f0-9]{32}\Z")
HEX64 = re.compile(r"[a-f0-9]{64}\Z")

class BadShape(ValueError):
    pass

def _typecheck(obj):
    if obj is None or type(obj) in (str, int, bool):
        return
    if type(obj) is list:
        for v in obj: _typecheck(v)
        return
    if type(obj) is dict:
        for k, v in obj.items():
            if type(k) is not str: raise BadShape("key")
            _typecheck(v)
        return
    raise BadShape("unsupported")

def canonical(obj):
    _typecheck(obj)
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")

def _key():
    try:
        st = os.stat(KEY, follow_symlinks=False)
        if not stat.S_ISREG(st.st_mode) or st.st_mode & 0o077:
            return None
        with open(KEY, "rb") as f:
            b = f.read(257)
        return b if 32 <= len(b) <= 256 else None
    except (OSError, ValueError):
        return None

def _pairs_unique(pairs):
    d = {}
    for k, v in pairs:
        if k in d: raise BadShape("duplicate key")
        d[k] = v
    return d

def attach(mission, role):
    """Gibt (NEUE Mission, Code) zurueck; bei Fehler Original unveraendert."""
    out = dict(mission)
    if "_provenance" in out: return out, "BAD_META"
    if role not in ROLES: return out, "ROLE_CONTEXT_MISSING"
    key = _key()
    if key is None: return out, "KEY_UNAVAILABLE"
    try:
        digest = hashlib.sha256(canonical(out)).hexdigest()
        meta = dict(FIXED, role=role, issued_at=int(time.time()),
                    nonce=secrets.token_hex(16), payload_sha256=digest)
        sig = hmac.new(key, PREFIX + canonical(meta), hashlib.sha256).hexdigest()
        out["_provenance"] = dict(meta, sig=sig)
        return out, "SHADOW_OK"
    except (BadShape, ValueError, TypeError, OverflowError):
        return dict(mission), "UNSUPPORTED_TYPE"

def verify(mission):
    """Nur pruefen: hat KEINE Auswirkung auf run_act/rec.ok."""
    if type(mission) is not dict: return "BAD_META"
    meta = mission.get("_provenance")
    if meta is None: return "LEGACY_UNSIGNED"
    if type(meta) is not dict: return "BAD_META"
    if set(meta) != set(FIXED) | {"role", "issued_at", "nonce", "payload_sha256", "sig"}:
        return "BAD_META"
    if any(meta[k] != v for k, v in FIXED.items()):
        if meta.get("kid") != KID: return "UNKNOWN_KID"
        if meta.get("aud") != FIXED["aud"]: return "WRONG_AUDIENCE"
        return "BAD_META"
    if meta.get("role") not in ROLES: return "BAD_META"
    if type(meta.get("issued_at")) is not int: return "BAD_META"
    if not HEX32.fullmatch(str(meta.get("nonce", ""))): return "BAD_META"
    if not HEX64.fullmatch(str(meta.get("payload_sha256", ""))): return "BAD_META"
    if not HEX64.fullmatch(str(meta.get("sig", ""))): return "BAD_META"
    now = int(time.time())
    if meta["issued_at"] > now + 120 or meta["issued_at"] < now - 3600:
        return "CLOCK_SKEW"
    key = _key()
    if key is None: return "KEY_UNAVAILABLE"
    try:
        body = {k: v for k, v in mission.items() if k != "_provenance"}
        digest = hashlib.sha256(canonical(body)).hexdigest()
        if not hmac.compare_digest(digest, meta["payload_sha256"]):
            return "BAD_PAYLOAD_HASH"
        bare = {k: v for k, v in meta.items() if k != "sig"}
        expected = hmac.new(key, PREFIX + canonical(bare), hashlib.sha256).hexdigest()
        return "SHADOW_OK" if hmac.compare_digest(expected, meta["sig"]) else "BAD_SIG"
    except (BadShape, ValueError, TypeError, OverflowError):
        return "UNSUPPORTED_TYPE"

def _audit(code, mission):
    """Log nur erlaubte Kurzfelder; keinerlei Extra-/Secret-/Cmd-Inhalte."""
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        if os.path.isfile(LOG) and os.stat(LOG).st_size > 5_000_000: return
        m = mission if type(mission) is dict else {}
        prov = m.get("_provenance")
        prov = prov if type(prov) is dict else {}
        rec = {"ts": int(time.time()), "code": code,
               "id": str(m.get("id", ""))[:90],
               "act": str(m.get("act", ""))[:40],
               "role": str(prov.get("role", "-"))[:20],
               "kid": str(prov.get("kid", "-"))[:40]}
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        if hasattr(os, "O_NOFOLLOW"): flags |= os.O_NOFOLLOW
        fd = os.open(LOG, flags, 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
    except Exception:
        pass  # Shadow-Audit darf nie die Mission aendern

def note_attach(code, mission):
    _audit(code, mission)

def shadow_check_path(path, parsed=None):
    """Prueft separate STRICT-Kopie der Mission; keine Mutation des Runner-Objekts."""
    status = "CHECK_EXCEPTION"
    info = parsed if type(parsed) is dict else {}
    try:
        if os.stat(path).st_size > 1_000_000:
            status = "BAD_META"
        else:
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read()
            info = json.loads(raw, object_pairs_hook=_pairs_unique,
                              parse_constant=lambda x: (_ for _ in ()).throw(BadShape(x)))
            status = verify(info)
    except (BadShape, ValueError, TypeError, OSError, UnicodeError):
        status = "BAD_META"
    except Exception:
        status = "CHECK_EXCEPTION"
    _audit(status, info)
    return status
