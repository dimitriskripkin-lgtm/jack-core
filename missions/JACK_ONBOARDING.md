# JACK Onboarding — Stand 2026-08-25 (Honor live)

Dokument für die **nächste KI** und für Dima. Honor-Live ist Wahrheit. GitHub `dimitriskripkin-lgtm/jack-core` ist **älter** als das Gerät.

Operator: **Dima**. Sprache: Deutsch, klar, kein Fachchinesisch im Chat mit ihm. Keine Emojis außer er will sie.

---

## 1. Wer mit wem redet

```
Dima  --Telegram-->  jack_telegram.py (Honor Termux)
                         |  jack_chat_router  FACT / EXPLAIN / DIAG / TALK
                         |  Groq gpt-oss-120b nur TALK + optionales [[LANE:]]
                         v
                    Tools: fact_report, selfsee, explain, UI-Intent
                         |
              SSH alias xiaomi-jack  -->  Xiaomi 11T Pro (Executor)
```

Grok/Claude sitzen **nicht** auf dem Handy. Jeder Fix ist ein **HONOR-Termux-Block**, den Dima einfügt. Output kommt zurück als Paste.

---

## 2. Geräte und Netz

| Rolle | Gerät | Wie |
|---|---|---|
| Gehirn | Honor Magic8 Pro | Termux, runit, alle jack_*.py in \~/jack |
| Arm | Xiaomi 11T Pro, Modell 2107113SG | SSH xiaomi-jack, Port 8022 |
| Letzte gute IP | 10.229.239.131 | Wechselt am Hotspot. \~/.ssh/config + jack_net_discover.py |

Wichtige Lektion: Android-UI verbunden ist NICHT SSH. Waechter prueft oefter als Layer-3 haelt. Deadman = mtime von jack_overmind_result.json, Alarm nach 3h. Das ist nicht Cortex-Uptime. Fix: python3 \~/jack/jack_overmind_client.py

---

## 3. Dienste (runit)
Pfad: /data/data/com.termux/files/usr/var/service/

jack_telegram Chat+Voice
jack_cortex Gehirn-Loop
jack_waechter Waechter/Shadow-Fixer
jack_autolearn Pause 600s idle / 300s busy
jack_publisher Context, git push TOT
jack_focus_monitor Focus 15s
jack_missions Queue-Loop poll 30s  NEU

Stopp Loop: Datei \~/jack/missions/STOP
Tune: focus_sleep_s 15, genesis_skip true, autolearn_idle_s 600, autolearn_busy_s 300
Skills: auto_fix_* geloescht. play_sido_youtube_loop und WLAN-CANDIDATE DEFEKT. DBs WAL.

---

## 4. Chat-Spuren (Text und Stimme)
Modul jack_chat_router.py
1. classify() Umlaute ae/oe/ue VOR Strip
2. FACT: ist zustand, /status, kiste+steht, wie steht -> fact_report() Health KEIN Akku
3. EXPLAIN: overmind / deadman
4. DIAG: analysier essenz schau dich/mal eigenen code murks fehler verbesser guck dir anomalie xiaomi offline graceful
5. sonst TALK = Groq Kumpel, keine Sensoren
Groq-erste-Zeile [[LANE:FACT|DIAG|EXPLAIN|TALK]] muss apply_lane schlucken. Tags nie im Chat.
Selfsee: Scan + Knoepfe nur wenn Act nicht recheck. Execute: recheck overmind_refresh fix_send chat_gate fix_ui
Voice: gleicher Router, keine Inline-Buttons.

---

## 5. Chrome-Falle
handle_ui_intent startete Google bei interessiert und such nach.
Trigger jetzt NUR: forsch, recherch, google, suche im web, im internet.
Missionen 003 004 014 030 031 048 muessen PASS bleiben.
send() nimmt nur Text. send(chat_id) war tot, 8 Stellen geflickt.

---

## 6. Missions-Loop
python3 /data/data/com.termux/files/home/jack/jack_mission_runner.py once
pending -> done|fail, logs/<id>.json
Acts erlaubt: fact diag no_chrome_src ui_none classify_is compile_ok explain_ok sv_ok
Verboten: ssh_exec git_push chrome groq_as_actor sv_restart_random write_outside_missions
001-050 ALLE PASS, fail leer. Dienst jack_missions run.
Beispiel: {"id":"051","act":"classify_is","text":"Ist Zustand?","expect":"FACT"}
GitHub Hahn zu bis Dima sagt auf. JACK pusht nicht jack-core. Missions-Repo pull -> pending.

---

## 7. Angefasst
jack_talk.py ist_zustand Health
jack_chat_router.py 4 Spuren fact_report apply_lane
jack_selfsee.py Scan Knoepfe
jack_exec.py Chrome-Trigger eng
jack_telegram.py send(chat_id)->send(  und chat_gate vor Deep-Nav
jack_publish.py HASH skip, git push = true
jack_autolearn_loop.py genesis skip Pause 600/300 BLOCK3
jack_focus_monitor.py 15s
\~/.ssh/config ControlPersist 600s
jack_hey.py ffmpeg NC
jack_persona.md Kumpel Verbote Temp/Schicht
jack_groq_bridge.py temp 0.55 soll
jack_tuev7.py jack_net_discover.py jack_mission_runner.py + runit jack_missions
Live weicht von GitHub ab. Vor Patch 20 Zeilen dumpen.

---

## 8. Anweisung naechste KI
1. Keine 5-Zeilen-Nadeln an jack_telegram.py. Neue Faehigkeit = Act + Mission.
2. Compile + Import jack_voice_processor wenn telegram neu + sv status jack_telegram
3. Telegram-Tests: EIN Satz pro Block
4. Groq sortiert, Python handelt. Kein Traegerwort-Theater.
5. FAIL = Stopp Queue
6. Wort sleep vermeiden (Wakelock)
7. Dollar in Honor-Bloecken vermeiden
8. Grosse wenige Bloecke, Dima faehrt
9. Kein von oben, kein was liegt an, keine Temperatur
10. GitHub nur Missions-Kanal
Erster Check: python3 \~/jack/jack_mission_runner.py once ; sv status .../jack_telegram ; sv status .../jack_missions ; python3 \~/jack/jack_health.py
J=/data/data/com.termux/files/home/jack

---

## 9. Roadmap noch NICHT in der Queue
Bald mit Dima: Live-Telegram-Satz als Mission, Voice DIAG, file_has Persona VERBOTEN, hb_ok Heartbeat, overmind_refresh nur wenn mtime>3h
GitHub-Loop andere KI:
1. Hahn auf, Repo nur missions/
2. KI pending JSON push
3. Honor git pull -> \~/jack/missions/pending/
4. jack_missions schreibt logs + done|fail
5. Logs zurueck (Remote logs/ oder Paste)
6. KI liest Log, naechste oder Stopp
7. Groq darf KEINE Missionstexte schreiben (schreibt such nach -> Chrome)
8. Deckel max N, STOP-Datei, kein SSH-Act
Nicht anfassen: git push jack-context, FAST_CMDS Dispatcher-Rewrite, Takeout, Genesis an, Monkey, Shizuku erzwingen

---

## 10. Ist-Zustand (Loop 047/024/012)
SSH Xiaomi OK
Focus 15s Genesis skip Idle 600s
Marks jack_hey jack_voice jack_publish jack_autolearn_loop ja
Dienste telegram cortex waechter autolearn publisher focus_monitor missions = run
Git-Push tot
Overmind \~1.5h (Schwelle 3h, Zahl driftet)
Chrome-Trigger clean
Queue leer fail leer
Missionen 001-050 PASS

---

## 11. GitHub-Loop 5 Schritte
1. Repo jack-missions: pending/ done/ logs/ README
2. Honor jack_mission_pull.py: git pull && cp pending/*.json \~/jack/missions/pending/  ohne push
3. Probe 051 KI push, Dima pull+once, Log zurueck
4. PASS: Dienst darf pull, Act git_pull_missions allowlist
5. FAIL: KI sieht fail/, Fix oder Stopp. Kein stilles Weiter.

---

## 12-18. Missionen 001-050 PASS
001 fact  002 diag  003 no_chrome_src  004 ui_none such nach Fehlern im Bot
005 Murks DIAG  006 Kiste FACT  007 Fehler DIAG  008 Ist Zustand FACT
009 eigenen Code DIAG  010 overmind EXPLAIN  011 Smalltalk TALK
012 fact  013 diag  014 ui_none interessiert  015 no_chrome_src
016 compile_ok  017 explain_ok  018 sv telegram  019 TALK  020 ui_none
021 sv missions  022 sv telegram  023 compile  024 fact
025-028 FACT DIAG EXPLAIN TALK  029 diag  030-031 ui_none  032 chrome  033 explain
034-037 sv waechter cortex autolearn publisher
038 eigenen Code DIAG  039 overmind EXPLAIN  040 compile runner  041 DEADMAN EXPLAIN
042 sv focus  043 sv missions  044-045 schau dich/essenz DIAG  046 tag TALK
047 fact  048 ui_none youtube (None, App-Start anderes Tor)  049 xiaomi offline DIAG  050 chrome

Dateien: jack_telegram.py \~1549 spaghetti FAST_CMDS tot; jack_talk.py; jack_chat_router.py; jack_selfsee.py; jack_exec.py Chrome-Tor; jack_groq_bridge.py; jack_persona.md; jack_health.py; jack_overmind_client.py; jack_net_discover.py; jack_publish.py; jack_autolearn_loop.py; jack_mission_runner.py; jack_tuev7.py; \~/jack/missions/; \~/.ssh/config Host xiaomi-jack Port 8022 Persist 600s

Fallen: 4 Tests in EINER Telegram-Nachricht; Needle miss; Umlaut; such nach vor Router; LANE-Tags im Chat; FACT=Akku; SIGALRM 15s; JSON literal backslash-n; sv ohne sv-enable; GEPUSHT-Luege

051+ darf: sv_ok, classify echte Saetze, file_has VERBOTEN, compile_ok, ui_none neue Verben. NICHT: git_push, ssh su, am start, google.
Ton: Werkzeug, Operator Dima, ein Ziel, FAIL sagen, Copy-Button.
