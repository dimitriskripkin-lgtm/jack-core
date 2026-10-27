# JACK_TUNE_SPOTIFY M1 (Kap 306) Spotify OAuth/PKCE. JACK_TUNE_SPOTIFYEXPORT: client_id liest export-Format, Offline-Modul. Standardbibliothek. Keine Aktion beim Import.
import base64, hashlib, http.server, json, os, pathlib, secrets, time
import urllib.parse, urllib.request

ROOT=pathlib.Path.home()/"jack"
TOKEN=ROOT/".spotify_token"
SCOPES="playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private user-read-recently-played user-library-read user-top-read"  # JACK_TUNE_SPOTIFYTOP: Herz-Songs + Topliste

def client_id():
    file=pathlib.Path.home()/".jack_secrets"
    if not file.is_file():raise RuntimeError("Spotify-Credentials fehlen")
    for line in file.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k,v=line.split("=",1)
            if k.strip().replace("export ","",1).strip()=="SPOTIFY_CLIENT_ID":return v.strip().strip('"').strip("'")
    raise RuntimeError("SPOTIFY_CLIENT_ID fehlt")

def _store(data):
    d=dict(data)
    d["expires_at"]=time.time()+int(d.get("expires_in",3600))
    if not d.get("refresh_token") and TOKEN.exists():
        d["refresh_token"]=json.loads(TOKEN.read_text())["refresh_token"]
    TOKEN.parent.mkdir(parents=True,exist_ok=True)
    temp=TOKEN.with_name("."+TOKEN.name+"."+secrets.token_hex(4)+".tmp")
    try:
        with os.fdopen(os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),"w") as f:
            json.dump(d,f)
        os.replace(temp,TOKEN)
        os.chmod(TOKEN,0o600)
    finally:
        if temp.exists():temp.unlink()
    return d

def _exchange(fields):
    data=urllib.parse.urlencode(fields).encode()
    req=urllib.request.Request("https://accounts.spotify.com/api/token",data=data,
        headers={"Content-Type":"application/x-www-form-urlencoded"},method="POST")
    with urllib.request.urlopen(req,timeout=15) as r:return json.load(r)

def anmelden():
    """Expliziter Login, nur 127.0.0.1:8765, maximal 120 Sekunden."""
    verifier=secrets.token_urlsafe(64); state=secrets.token_urlsafe(20)
    challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    redirect="http://127.0.0.1:8765/callback"
    params={"client_id":client_id(),"response_type":"code","redirect_uri":redirect,
            "scope":SCOPES,"state":state,"code_challenge_method":"S256","code_challenge":challenge}
    code=[]
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*a):pass
        def do_GET(self):
            uri=urllib.parse.urlparse(self.path); q=urllib.parse.parse_qs(uri.query)
            if uri.path!="/callback" or q.get("state",[None])[0]!=state:
                self.send_error(400);return
            code.append(q.get("code",[None])[0])
            self.send_response(200);self.end_headers()
            self.wfile.write(b"JACK Spotify: Anmeldung empfangen. Fenster schliessen.")
    server=http.server.HTTPServer(("127.0.0.1",8765),Handler);server.timeout=120
    try:
        _url="https://accounts.spotify.com/authorize?"+urllib.parse.urlencode(params)
        print("Spotify-Anmeldung oeffnet sich im Browser. Falls nicht, diesen Link oeffnen:\n"+_url)
        try:
            import subprocess; subprocess.run(["termux-open-url",_url],timeout=10)  # JACK_TUNE_SPOTIFYOPEN
        except Exception:
            pass
        server.handle_request()
    finally:server.server_close()
    if not code or not code[0]:raise RuntimeError("Anmeldung fehlt/abgebrochen")
    _store(_exchange({"grant_type":"authorization_code","code":code[0],
                      "redirect_uri":redirect,"client_id":client_id(),"code_verifier":verifier}))
    return True

def refresh():
    t=json.loads(TOKEN.read_text(encoding="utf-8"))
    if not t.get("refresh_token"):raise RuntimeError("Kein Refresh-Token")
    d=_exchange({"grant_type":"refresh_token","refresh_token":t["refresh_token"],
                 "client_id":client_id()})
    d.setdefault("refresh_token",t["refresh_token"])
    _store(d)

def access():
    if not TOKEN.is_file():raise RuntimeError("Spotify erst anmelden")
    data=json.loads(TOKEN.read_text(encoding="utf-8"))
    if time.time()>=float(data.get("expires_at",0))-60:
        refresh()
        data=json.loads(TOKEN.read_text(encoding="utf-8"))
    return data["access_token"]
