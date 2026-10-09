# JACK_TUNE_OAUTH -- minimaler OAuth-2.1-Server (Authorization Code + PKCE S256) NUR fuer Rolle chatgpt.
# Freigabe nie anonym: jede Autorisierung braucht eine PIN, die per Telegram nur an Dima geht.
# Tokens nur als SHA-256-Hash in .jack_oauth.json (chmod 600). Notaus: Datei .oauth_off.
import os, json, time, hashlib, secrets, threading, html
from urllib.parse import urlparse, urlencode, urlunparse, parse_qsl

JACK_HOME = os.environ.get("JACK_OAUTH_DIR") or os.path.expanduser("~/jack")
STATE = JACK_HOME + "/.jack_oauth.json"
OFF = JACK_HOME + "/.oauth_off"
BASE = os.environ.get("JACK_OAUTH_BASE") or "https://mcp.jack-mcp-cloudflare.bid"
ROLE = "chatgpt"
SCOPE = "jack"
HOSTS = {"chatgpt.com", "chat.openai.com", "platform.openai.com"}
T_CODE, T_ACCESS, T_REFRESH, T_PENDING = 300, 3600, 30 * 86400, 600
MAX_CLIENTS, MAX_PIN_TRIES = 5, 3
RL = {"reg": (10, 3600), "auth": (6, 3600)}
PUBLIC = ("/authorize", "/token", "/register", "/oauth/consent",
          "/.well-known/oauth-authorization-server", "/.well-known/oauth-protected-resource",
          "/.well-known/openid-configuration")
_lock = threading.RLock()
_cache = {"m": None, "d": None}


def _h(s):
    return hashlib.sha256(s.encode()).hexdigest()


def _empty():
    return {"clients": {}, "pending": {}, "codes": {}, "access": {}, "refresh": {}, "rl": {}}


def _load():
    with _lock:
        try:
            m = os.stat(STATE).st_mtime_ns
            if _cache["m"] == m and _cache["d"] is not None:
                return _cache["d"]
            d = json.load(open(STATE))
            for k, v in _empty().items():
                d.setdefault(k, v)
        except Exception:
            d = _empty()
            m = None
        _cache.update(m=m, d=d)
        return d


def _save(d):
    with _lock:
        tmp = STATE + ".tmp"
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(d, f)
        os.replace(tmp, STATE)
        os.chmod(STATE, 0o600)
        _cache.update(m=os.stat(STATE).st_mtime_ns, d=d)


def _gc(d):
    now = time.time()
    for k in ("pending", "codes", "access", "refresh"):
        d[k] = {a: b for a, b in d[k].items() if b.get("exp", 0) > now}


def _rl(d, key):
    n, w = RL[key]
    now = time.time()
    L = [t for t in d["rl"].get(key, []) if now - t < w]
    if len(L) >= n:
        d["rl"][key] = L
        return False
    L.append(now)
    d["rl"][key] = L
    return True


def _audit(txt):
    try:
        import jack_mcp_auth as a
        a.audit(ROLE, "oauth", "", "ja", txt[:80])
    except Exception:
        pass


def _tg(text):
    try:
        import jack_telegram
        jack_telegram.send(text)
        return True
    except Exception:
        return False


def is_off():
    return os.path.exists(OFF)


def is_public(path):
    if is_off():
        return False
    return any(path == p or path.startswith(p + "/") for p in PUBLIC)


def role_of_token(tok):
    """Rolle zu einem OAuth-Access-Token, sonst None. Fail-closed."""
    try:
        if is_off() or not tok:
            return None
        e = _load()["access"].get(_h(tok))
        if e and e.get("exp", 0) > time.time():
            return ROLE
    except Exception:
        pass
    return None


def resource_metadata_url():
    return BASE + "/.well-known/oauth-protected-resource/mcp"


def _ok_redirect(u):
    p = urlparse(str(u))
    return p.scheme == "https" and p.hostname in HOSTS and not p.fragment and not p.query and not p.username


def _issue(d, client_id, scopes, resource, with_refresh=True):
    a = secrets.token_urlsafe(32)
    d["access"][_h(a)] = {"client": client_id, "exp": time.time() + T_ACCESS}
    r = None
    if with_refresh:
        r = secrets.token_urlsafe(32)
        d["refresh"][_h(r)] = {"client": client_id, "scopes": scopes, "resource": resource,
                               "exp": time.time() + T_REFRESH}
    return a, r


def build_provider():
    from mcp.server.auth.provider import (AuthorizationCode, RefreshToken, AccessToken,
                                          RegistrationError, TokenError, AuthorizeError)
    from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

    class P:
        async def get_client(self, client_id):
            c = _load()["clients"].get(client_id)
            return OAuthClientInformationFull.model_validate(c) if c else None

        async def register_client(self, info):
            with _lock:
                d = _load()
                _gc(d)
                uris = [str(u) for u in (info.redirect_uris or [])]
                if not uris or not all(_ok_redirect(u) for u in uris):
                    raise RegistrationError("invalid_redirect_uri", "redirect_uri nicht erlaubt")
                if len(d["clients"]) >= MAX_CLIENTS or not _rl(d, "reg"):
                    raise RegistrationError("invalid_client_metadata", "Limit erreicht")
                if info.client_secret:
                    info.client_secret = None
                d["clients"][info.client_id] = json.loads(info.model_dump_json())
                _save(d)
                _audit("client registriert")

        async def authorize(self, client, params):
            with _lock:
                d = _load()
                _gc(d)
                if not _rl(d, "auth"):
                    _save(d)
                    raise AuthorizeError("access_denied", "zu viele Anfragen")
                rid, pin = secrets.token_urlsafe(24), "%06d" % secrets.randbelow(10 ** 6)
                d["pending"][rid] = {
                    "client": client.client_id, "pin": _h(pin), "tries": 0,
                    "exp": time.time() + T_PENDING,
                    "params": json.loads(params.model_dump_json())}
                name = (client.client_name or "Client")[:40]
                if not _tg("OAuth-Freigabe: %s will Lesezugriff auf JACK (Rolle chatgpt). "
                           "PIN: %s (10 Min, 3 Versuche). Nicht du? Ignorieren." % (name, pin)):
                    d["pending"].pop(rid, None)
                    _save(d)
                    raise AuthorizeError("temporarily_unavailable", "Freigabekanal nicht erreichbar")
                _save(d)
                _audit("authorize angefragt")
            return BASE + "/oauth/consent?" + urlencode({"req": rid})

        async def load_authorization_code(self, client, authorization_code):
            e = _load()["codes"].get(_h(authorization_code))
            if not e or e["client"] != client.client_id or e["exp"] < time.time():
                return None
            return AuthorizationCode(code=authorization_code, scopes=e["scopes"], expires_at=e["exp"],
                                     client_id=e["client"], code_challenge=e["challenge"],
                                     redirect_uri=e["redirect_uri"],
                                     redirect_uri_provided_explicitly=e["explicit"],
                                     resource=e.get("resource"))

        async def exchange_authorization_code(self, client, authorization_code):
            with _lock:
                d = _load()
                if d["codes"].pop(_h(authorization_code.code), None) is None:
                    raise TokenError("invalid_grant", "Code schon benutzt")
                a, r = _issue(d, client.client_id, [SCOPE], authorization_code.resource)
                _save(d)
                _audit("token ausgestellt")
            return OAuthToken(access_token=a, expires_in=T_ACCESS, scope=SCOPE, refresh_token=r)

        async def load_refresh_token(self, client, refresh_token):
            e = _load()["refresh"].get(_h(refresh_token))
            if not e or e["client"] != client.client_id or e["exp"] < time.time():
                return None
            return RefreshToken(token=refresh_token, client_id=e["client"], scopes=e["scopes"],
                                expires_at=int(e["exp"]), resource=e.get("resource"))

        async def exchange_refresh_token(self, client, refresh_token, scopes):
            with _lock:
                d = _load()
                if d["refresh"].pop(_h(refresh_token.token), None) is None:
                    raise TokenError("invalid_grant", "Refresh-Token ungueltig")
                a, r = _issue(d, client.client_id, [SCOPE], refresh_token.resource)
                _gc(d)
                _save(d)
                _audit("token rotiert")
            return OAuthToken(access_token=a, expires_in=T_ACCESS, scope=SCOPE, refresh_token=r)

        async def load_access_token(self, token):
            return AccessToken(token=token, client_id="chatgpt", scopes=[SCOPE]) if role_of_token(token) else None

        async def revoke_token(self, token):
            with _lock:
                d = _load()
                t = _h(token.token)
                d["access"].pop(t, None)
                d["refresh"].pop(t, None)
                _save(d)

    return P()


_PAGE = """<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>JACK Freigabe</title><body style="font-family:sans-serif;max-width:26em;margin:2em auto;padding:0 1em">
<h2>JACK Freigabe</h2><p>%s</p>%s</body>"""
_HDR = {"Cache-Control": "no-store", "X-Frame-Options": "DENY",
        "Content-Security-Policy": "frame-ancestors 'none'", "Referrer-Policy": "no-referrer"}


def build_routes():
    from starlette.routing import Route
    from starlette.responses import HTMLResponse, RedirectResponse
    from mcp.server.auth.routes import create_auth_routes, create_protected_resource_routes
    from mcp.server.auth.settings import ClientRegistrationOptions, RevocationOptions
    from pydantic import AnyHttpUrl
    prov = build_provider()

    def page(msg, form="", code=200):
        return HTMLResponse(_PAGE % (html.escape(msg), form), status_code=code, headers=_HDR)

    async def consent(request):
        if is_off():
            return page("Aus.", code=404)
        rid = request.query_params.get("req", "")
        with _lock:
            d = _load()
            _gc(d)
            p = d["pending"].get(rid)
            if not p:
                return page("Anfrage unbekannt oder abgelaufen.", code=400)
            if request.method == "GET":
                f = ('<form method=post><input name=pin inputmode=numeric autocomplete=off '
                     'maxlength=6 autofocus placeholder="PIN aus Telegram"> '
                     '<button>Freigeben</button></form>')
                return page("Gib die PIN ein, die Jack dir per Telegram geschickt hat.", f)
            form = await request.form()
            pin = str(form.get("pin", "")).strip()
            p["tries"] += 1
            if p["tries"] > MAX_PIN_TRIES:
                d["pending"].pop(rid, None)
                _save(d)
                return page("Zu viele Versuche. Anfrage verworfen.", code=403)
            if not secrets.compare_digest(_h(pin), p["pin"]):
                _save(d)
                return page("PIN falsch.", code=403)
            d["pending"].pop(rid, None)
            pr = p["params"]
            code = secrets.token_urlsafe(32)
            d["codes"][_h(code)] = {"client": p["client"], "scopes": [SCOPE], "exp": time.time() + T_CODE,
                                    "challenge": pr["code_challenge"], "redirect_uri": pr["redirect_uri"],
                                    "explicit": pr["redirect_uri_provided_explicitly"],
                                    "resource": pr.get("resource")}
            _save(d)
            _audit("freigegeben per PIN")
        u = urlparse(pr["redirect_uri"])
        q = dict(parse_qsl(u.query))
        q["code"] = code
        if pr.get("state"):
            q["state"] = pr["state"]
        return RedirectResponse(urlunparse(u._replace(query=urlencode(q))), status_code=302, headers=_HDR)

    routes = create_auth_routes(
        prov, AnyHttpUrl(BASE),
        client_registration_options=ClientRegistrationOptions(enabled=True, valid_scopes=[SCOPE], default_scopes=[SCOPE]),
        revocation_options=RevocationOptions(enabled=False))
    routes += create_protected_resource_routes(AnyHttpUrl(BASE + "/mcp"), [AnyHttpUrl(BASE)],
                                               scopes_supported=[SCOPE], resource_name="JACK")
    routes.append(Route("/oauth/consent", consent, methods=["GET", "POST"]))
    return routes


if __name__ == "__main__":
    import sys
    c = sys.argv[1] if len(sys.argv) > 1 else "list"
    d = _load()
    if c == "drop":
        for k in ("pending", "codes", "access", "refresh"):
            d[k] = {}
        if len(sys.argv) > 2 and sys.argv[2] == "alles":
            d["clients"] = {}
        _save(d)
        print("OAuth-Tokens widerrufen.")
    else:
        _gc(d)
        print({k: len(v) for k, v in d.items() if k != "rl"})
