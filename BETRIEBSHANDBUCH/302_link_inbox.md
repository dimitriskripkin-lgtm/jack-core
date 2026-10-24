# 302 Link-Inbox fuer Videos (23.10.2026)

Warum: Supadata ist als Connector in Claude (und ChatGPT) verbunden. Ein Video-Link reicht, damit Claude Metadaten + Transkript hat. Kurzer Weg vom Handy: in TikTok/Instagram/YouTube teilen -> JACK-Bot in Telegram.
Datei ~/jack/jack_linkinbox.py (JACK_TUNE_LINKINBOX): erkennt Links von tiktok.com, instagram.com, youtube.com, youtu.be, x.com, twitter.com, facebook.com, fb.watch (Domain-Ende geprueft, nottiktok.com.evil.de faellt durch). Schreibt je Link eine Zeile {ts,url,notiz,quelle,status} nach logs/link_inbox.jsonl (gitignored seit 23.10., vorher NICHT -> nachgetragen). Antwort im Chat: Fuer Claude gemerkt. /links zeigt die letzten 5.
jack_telegram.handle: Block vor dem Web-Ingest (Schritt 2). Andere Links laufen weiter ueber jack_web_ingest. Fehler werden per send gemeldet.
JACK ruft Supadata NICHT selbst auf (kein Key auf dem Geraet, Credits nur auf Claude/ChatGPT-Seite). Auswertung: Claude liest logs/link_inbox.jsonl per MCP read_file, ruft supadata_metadata/supadata_transcript, trennt gesprochen (Transkript) von gesehen (nur per supadata_extract, Credits).
Tests 11/11 offline, live 23.10. 15:20. Backup jack_telegram.py.bak_20261023_linkinbox. Neustart jack_telegram 15:20.
Offen: status neu->gelesen setzen, wenn Claude ausgewertet hat; ggf. Ergebnis-Cache (Quelle, Sprache, Transkript-Kurzfassung) gegen doppelte Credits.

## REGEL Supadata-Budget (Dima 23.10.2026, Zahlen laut supadata.ai/pricing 23.10.)
- Free-Tarif: 100 Credits pro MONAT (nicht pro Tag), kein Uebertrag, 1 Anfrage/s. Claude und ChatGPT teilen dasselbe Konto.
- Kosten: Metadaten 1, vorhandenes Transkript 1, KI-erzeugtes Transkript 2 je Videominute, extract (Bild) 5 je Minute (min 5), scrape/map 1.
- Ablauf je Video: erst supadata_metadata (1), dann supadata_transcript mit mode=native (1). Nur wenn kein Transkript da ist: generate, und nur bei kurzen Videos oder auf Dimas Wunsch. extract nur auf Dimas Wunsch.
- Faustregel: im Schnitt hoechstens 3 Videos pro Tag. Verbrauch je Abruf in der Antwort an Dima nennen.
- Erster Test 23.10. (Maserati, 3:28 Min, mode=auto): geschaetzt ca. 9 Credits (1 Metadaten + ca. 7 generiert + 1 Preisseite).
