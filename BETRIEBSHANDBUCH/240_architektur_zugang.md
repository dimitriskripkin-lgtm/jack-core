# 240 Architektur-Ueberblick Stand 08.10.2026 und Zugangsmodell (Plan)
## Schichten (von unten nach oben)
1. Geraete: HONOR (Host, kein Root, alle Dienste + MCP) / XIAOMI (Worker, Root, SSH-Alias xiaomi-jack, IP per DHCP, wird von jack_cortex.find_xiaomi gefunden: Cache .last_xiaomi_ip -> ssh-config -> Subnetz-Scan per UDP-Routentrick, Kap. 239).
2. Dienste (runit): telegram, cortex, waechter, autolearn, publisher, focus_monitor, missions (Runner), mcp, cloudflared.
3. Tuer nach aussen: MCP-Server (HTTPS ueber Cloudflare-Tunnel, Bearer-Token). Werkzeuge: Handbuch (start_hier, handbuch_index/-kapitel), read_file, create_mission, Arbeitsplatz/Kanal (buero, ap_notiz, ap_journal, ap_post, ap_lese, ap_claim).
4. Missions-Pipeline: create_mission -> missions/pending -> Runner -> done/fail. Nur Acts aus jack_acts.py (Whitelist, in drei Stellen gepflegt: jack_acts.py, Runner, MCP-Server). KEIN freies exec.
5. Handbuch-Gate: schreibende Missions nur mit Tages-Quittung (Beweis: Pflichtzettel + Kapitel gelesen).
6. Arbeitsplatz (Kap. 234): ARBEITSPLATZ/gemeinsam (Wahrheit fuer Regeln, Roadmap, Entscheidungen, Bugs) + BUEROS/{claude,grok,gemini}. Eigenes Buero frei, fremdes nur an eingang.md anhaengen.
7. Kanal (Kap. 235): Claude<->Grok Nachrichten, Claims, Not-Aus durch 10er-Zaehler und missions/STOP.
8. Pruefstand: jack_pyflakes_lauf.py (Kap. 236-238) findet Python-Fehler im Code.
## Eiserne Grenzen (unveraendert)
Kein freies exec, Groq nur TALK, kein Ollama auf dem Honor, keine Geheimnisse ausgeben/committen, Token-Rotation/Loeschen/Rechte-Erweiterung nur Dima.
## Zugangsmodell-Plan (Dima-Wunsch 08.10.2026: Claude soll ohne Terminal-Output selbst nachsehen koennen)
Stufe R (nur lesen, vorgeschlagen): feste, parametrisierte Lese-Acts statt Shell: log_tail(dienst, n), git_status_ro, git_scan_ro (Geheimnis-Muster, nur Dateinamen), pyflakes_ro, ps_ro, ip_probe_ro. Pfade nur unter ~/jack, Denylist: config.ini, .ssh, *token*, *.db-Inhalte. Jede Ausgabe gekuerzt und geschwaerzt.
Stufe S (begrenztes Schreiben, spaeter): git commit/push nur nach gruener Geheimnis-Pruefung und mit Dima-Freigabe-Flag; Dienst-Restarts bleiben auf Whitelist.
Stufe A (Autonomie, nur auf Dimas Go): Arbeitsliste + Tagesbudget + Morgenbericht (Kap. 'autonomer Dauerlauf').
Voraussetzung vor Stufe R: Token-Rotation durch Dima und ein eigener Token pro KI-Rolle (claude/grok/gemini) mit Scope + Audit-Log jedes Aufrufs. Der Token steht nie im Chat.
