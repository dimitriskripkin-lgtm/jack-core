// JACK_TUNE_MUSIKGUT (28.10.2026, Claude, Kap 307): fuellt "Musik gut (wiederhergestellt)" im n8n-Container (Xiaomi).
// Zugang = n8n-Credential jackYouTube00001 (nur im Speicher, Exportdatei wird sofort geloescht). Gibt keine Geheimnisse aus.
// v2 03:58: failedPrecondition (geloeschtes/privates Video) -> 1x nach 4 s wiederholen, dann ueberspringen.
const fs = require("fs"), cp = require("child_process"), H = process.env.HOME, R = H + "/yt_rettung";
const N = H + "/jack_n8n/node_modules/n8n/bin/n8n";
const MAX = +(process.argv[2] || 185);
const st = fs.existsSync(R + "/state.json") ? JSON.parse(fs.readFileSync(R + "/state.json", "utf8")) : { pos: 0, ok: 0, skip: [] };
const ids = fs.readFileSync(R + "/ids.txt", "utf8").split(/\s+/).filter(x => /^[\w-]{11}$/.test(x));
const save = () => fs.writeFileSync(R + "/state.json", JSON.stringify(st), { mode: 0o600 });
const sleep = ms => new Promise(s => setTimeout(s, ms));
(async () => {
  if (st.pos >= ids.length) { console.log("FERTIG (schon) | drin", st.ok, "| uebersprungen", st.skip.length, "| playlist", st.playlistId); return; }
  const tmp = R + "/.c.json";
  let c;
  try {
    cp.execFileSync(N, ["export:credentials", "--id=jackYouTube00001", "--decrypted", "--output=" + tmp], { stdio: "ignore", timeout: 120000 });
    const k = JSON.parse(fs.readFileSync(tmp, "utf8")); c = (Array.isArray(k) ? k[0] : k).data;
  } catch (e) { console.log("FEHLER export"); process.exit(2); }
  finally { fs.rmSync(tmp, { force: true }); }
  const rt = c && c.oauthTokenData && c.oauthTokenData.refresh_token;
  if (!rt) { console.log("FEHLER kein refresh_token (YouTube neu verbinden)"); process.exit(3); }
  const tr = await fetch("https://oauth2.googleapis.com/token", { method: "POST", headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ client_id: c.clientId, client_secret: c.clientSecret, refresh_token: rt, grant_type: "refresh_token" }) });
  const tj = await tr.json().catch(() => ({}));
  if (!tj.access_token) { console.log("FEHLER token", tr.status, String(tj.error || "")); process.exit(4); }
  const A = { authorization: "Bearer " + tj.access_token, "content-type": "application/json" };
  const API = "https://www.googleapis.com/youtube/v3/";
  if (!st.playlistId) {
    const r = await fetch(API + "playlists?part=snippet,status", { method: "POST", headers: A, body: JSON.stringify({
      snippet: { title: "Musik gut (wiederhergestellt)", description: "Von JACK aus dem YouTube-Verlauf rekonstruiert (Stand vor Aug 2025), meistgehoert zuerst." },
      status: { privacyStatus: "private" } }) });
    const j = await r.json().catch(() => ({}));
    if (!j.id) { console.log("FEHLER playlist", r.status, JSON.stringify((j.error && j.error.errors) || "").slice(0, 200)); process.exit(5); }
    st.playlistId = j.id; save(); console.log("playlist angelegt", j.id);
  }
  let n = 0, neu = 0, folge = 0, grund = "tageslimit";
  while (st.pos < ids.length && n < MAX) {
    const v = ids[st.pos];
    const r = await fetch(API + "playlistItems?part=snippet", { method: "POST", headers: A,
      body: JSON.stringify({ snippet: { playlistId: st.playlistId, resourceId: { kind: "youtube#video", videoId: v } } }) });
    n++;
    if (r.ok) { st.ok++; st.pos++; neu++; folge = 0; save(); await sleep(250); continue; }
    const j = await r.json().catch(() => ({}));
    const why = (((j.error && j.error.errors) || [])[0] || {}).reason || String(r.status);
    if (/quota|dailyLimit|rateLimit/i.test(why)) { grund = "quota"; break; }
    if (/failedPrecondition|backendError/i.test(why) && st.retry !== v) { st.retry = v; await sleep(4000); continue; }
    if (r.status === 404 || /videoNotFound|forbidden|notFound|failedPrecondition/i.test(why)) {
      st.skip.push(v + ":" + why); st.pos++; folge++; save();
      if (folge >= 8) { grund = "8 Fehler am Stueck (" + why + "), angehalten"; break; }
      continue;
    }
    grund = "fehler " + r.status + " " + why; break;
  }
  if (st.pos >= ids.length) grund = "FERTIG";
  console.log("heute neu", neu, "| drin", st.ok, "| uebersprungen", st.skip.length, "| stand", st.pos + "/" + ids.length, "| stopp:", grund, "| playlist", st.playlistId);
})().catch(e => { console.log("FEHLER", e.message); process.exit(9); });
