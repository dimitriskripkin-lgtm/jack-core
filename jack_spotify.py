# JACK_TUNE_SPOTIFY M1 (Kap 306) JACK Spotify – Offline-Entwurf, Standardbibliothek. Keine APIs beim Import.
import collections, datetime, json, os, pathlib, random, re, secrets, time
import urllib.error, urllib.parse, urllib.request
import jack_spotify_oauth as oauth

ROOT=pathlib.Path.home()/"jack"
BACKUPS=ROOT/"logs"/"spotify_backup"
VERLAUF=ROOT/"logs"/"spotify_verlauf.jsonl"
BASE="https://api.spotify.com/v1"

def _id(x):
    if not isinstance(x,str) or not re.fullmatch(r"[A-Za-z0-9]{1,64}",x):
        raise ValueError("Ungueltige Playlist-ID")
    return x

def _save(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    os.chmod(path.parent,0o700)
    temp=path.with_name("."+path.name+"."+secrets.token_hex(5)+".tmp")
    try:
        with os.fdopen(os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),"w") as f:
            json.dump(data,f,ensure_ascii=False,indent=2)
        os.replace(temp,path);os.chmod(path,0o600)
    finally:
        if temp.exists():temp.unlink()

def _http(method,path,body=None,params=None,reauthed=False,retried=False):
    if not path.startswith("/") or path.startswith("//"):
        raise ValueError("Nur Spotify-API-Pfade")
    url=BASE+path
    if params:url+="?"+urllib.parse.urlencode(params)
    data=None if body is None else json.dumps(body).encode()
    headers={"Authorization":"Bearer "+oauth.access()}
    if data is not None:headers["Content-Type"]="application/json"
    request=urllib.request.Request(url,data=data,headers=headers,method=method)
    try:
        with urllib.request.urlopen(request,timeout=15) as response:
            raw=response.read()
        return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        if exc.code==401 and not reauthed:
            oauth.refresh()
            return _http(method,path,body,params,True,retried)
        if exc.code==429 and not retried:
            try:
                err=json.loads(exc.read().decode("utf-8"))
                if err.get("error",{}).get("reason")=="QUOTA_EXCEEDED":
                    raise RuntimeError("Spotify-Quota aufgebraucht")
            except ValueError:pass
            try:wait=int(exc.headers.get("Retry-After","2"))
            except (ValueError,TypeError):wait=16
            if 0<=wait<=15:
                time.sleep(wait)
                return _http(method,path,body,params,reauthed,True)
        raise RuntimeError("Spotify HTTP "+str(exc.code)) from None

def _pages(path):
    off=0
    while True:
        page=_http("GET",path,params={"limit":50,"offset":off})
        arr=page.get("items") or []
        yield from arr
        off+=len(arr)
        if not arr or not page.get("next"):break

def playlists():
    return list(_pages("/me/playlists"))

def items(pid):
    return list(_pages("/playlists/"+_id(pid)+"/items"))

def _uris(rows):
    result=[]
    for row in rows:
        if row.get("is_local"):raise ValueError("Lokale Titel nicht sicher sortierbar")
        uri=(row.get("item") or row.get("track") or {}).get("uri")
        if not isinstance(uri,str) or not re.fullmatch(r"spotify:(track|episode):[A-Za-z0-9]+",uri):
            raise ValueError("Titel ohne sichere URI")
        result.append(uri)
    return result

def _key(row,name):
    song=row.get("item") or row.get("track") or {}
    d={"titel":song.get("name") or "",
       "kuenstler":", ".join(a.get("name","") for a in song.get("artists",[])),
       "album":(song.get("album") or {}).get("name") or "",
       "hinzugefuegt":row.get("added_at") or "",
       "dauer":song.get("duration_ms") or 0}
    x=d[name]
    return x.casefold() if isinstance(x,str) else x

def _reorder(pid,current,target,snapshot):
    current=list(current);changed=0
    for i,want in enumerate(target):
        pos=current.index(want)
        if pos==i:continue
        response=_http("PUT","/playlists/"+pid+"/items",
            {"range_start":pos,"insert_before":i,"range_length":1,
             "snapshot_id":snapshot})
        snapshot=response.get("snapshot_id")
        if not snapshot:raise RuntimeError("Snapshot fehlt – Abbruch")
        current.insert(i,current.pop(pos));changed+=1
    return changed

def sortiere(pid,schluessel,absteigend=False,bestaetigt=False):
    pid=_id(pid)
    if schluessel not in {"titel","kuenstler","album","hinzugefuegt","dauer","zufall"}:
        raise ValueError("Unbekannter Sortierschluessel")
    if not bestaetigt:raise PermissionError("Bitte vorher bestaetigen")
    entries=items(pid);uris=_uris(entries)
    meta=_http("GET","/playlists/"+pid)
    if not meta.get("snapshot_id"):raise RuntimeError("Snapshot fehlt")
    order=list(range(len(entries)))
    if schluessel=="zufall":random.SystemRandom().shuffle(order)
    else:order.sort(key=lambda i:_key(entries[i],schluessel),reverse=absteigend)
    if order==list(range(len(entries))):
        return {"verschoben":0,"backup":None}
    backup=BACKUPS/(pid+"_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")+".json")
    _save(backup,{"playlist_id":pid,"uris":uris,"snapshot_id":meta["snapshot_id"]})
    moves=_reorder(pid,list(range(len(entries))),order,meta["snapshot_id"])
    return {"verschoben":moves,"backup":str(backup)}

def zurueck(pid,bestaetigt=False):
    pid=_id(pid)
    if not bestaetigt:raise PermissionError("Rueckgaengig nur nach Bestaetigung")
    backups=sorted(BACKUPS.glob(pid+"_*.json"))
    if not backups:raise FileNotFoundError("Keine Sicherung")
    old=json.loads(backups[-1].read_text(encoding="utf-8"))["uris"]
    current=_uris(items(pid))
    if collections.Counter(old)!=collections.Counter(current):
        raise RuntimeError("Playlist zwischenzeitlich geaendert – Abbruch")
    pools=collections.defaultdict(list)
    for i,uri in enumerate(current):pools[uri].append(i)
    target=[pools[uri].pop(0) for uri in old]
    snap=_http("GET","/playlists/"+pid)["snapshot_id"]
    return _reorder(pid,list(range(len(current))),target,snap)

def verlauf_holen():
    """GET /me/player/recently-played offiziell dokumentiert; App-Zugriff ungetestet."""
    page=_http("GET","/me/player/recently-played",params={"limit":50})
    VERLAUF.parent.mkdir(parents=True,exist_ok=True)
    known=set()
    if VERLAUF.exists():
        for line in VERLAUF.read_text(encoding="utf-8").splitlines():
            try:known.add(json.loads(line)["played_at"])
            except (ValueError,KeyError):pass
    n=0
    with open(VERLAUF,"a",encoding="utf-8") as f:
        os.chmod(VERLAUF,0o600)
        for row in page.get("items",[]):
            stamp=row.get("played_at")
            if not stamp or stamp in known:continue
            song=row.get("track") or row.get("item") or {}
            f.write(json.dumps({"played_at":stamp,"uri":song.get("uri"),
                "name":song.get("name")},ensure_ascii=False)+"\n")
            known.add(stamp);n+=1
    return n
