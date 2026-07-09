# JACK - Architektur und Bauanleitung

## Was JACK ist
Persoenliche KI-Betriebsschicht auf zwei Android-Geraeten (Termux).
Honor Magic8 Pro = Gehirn/Host. Xiaomi 11T Pro = Arm/Executor via SSH.

## Die 7 Schichten (von unten)
1. FUNDAMENT: Termux, Magisk (Root Xiaomi), SSH-Ruecken (10.234.166.131:8022, Key ~/.ssh/id_jack)
2. PERSISTENZ: jack_errors.db, jack_memory.db (+sqlite-vec), jack_identity.json, ~/.jack_secrets
3. MODELL-ZUGANG: jack_gemini_bridge (Gemini 2.5 Flash), Ollama (llama3.2:3b + nomic-embed-text)
4. GEDAECHTNIS (MemGPT-3-Tier): Core=identity.json | Recall=Verlauf | Archival=Vektorsuche | Selbstlernen=jack_learn (2h)
5. DENKEN: talk_to_gemini() fuehrt Core+Recall+Archival+Live-Status zusammen, ruft Gemini
6. HAENDE (alle gegated): jack_write (Werkstatt+Bestaetigung), jack_coder (Code schreiben+ausfuehren, Risiko-Gate), jack_patch (SEARCH/REPLACE Selbstumbau), jack_bug_fixer
7. AUTONOM: jack_cortex (Watchdog+Heilung), jack_autolearn (Heartbeat 2h)

## Interfaces
Telegram-Bot @JackDimaChat_bot: Text + Sprache (whisper.cpp -> Gemini -> ElevenLabs)
Befehle: /status /errors /code <aufgabe> /run /werkstatt

## Sicherheitsprinzipien
- Werkstatt-Sandbox (~/jack_werkstatt), kein Ausbruch moeglich
- HIGH_RISK-Muster blockieren Ausfuehrung (loeschen/netz/secrets)
- Zwei-Schritt-Bestaetigung fuer Schreiben
- Ehrlichkeit: nie behaupten was er nicht kann, Live-Daten statt Gedaechtnis-Raten
- Chat-Code fasst nie die lebenden Module an - nur ueber Patch-Gate

## Offene Baustellen (Prioritaet)
1. PFLICHT: Keys erneuern (im Chat exponiert) - Telegram via BotFather, Gemini via Google-Konsole
2. Xiaomi-SSH dauerhaft gegen Android-Kill absichern (Wake-Lock/Magisk)
3. Bug-Fixer einmal live an kontrolliertem Fehler testen
4. Entscheidungs-Protokoll (Nachvollziehbarkeit)
5. Source/Confidence im Gedaechtnis auswerten (selbstreinigend)

## Naechstes Level
- AUGEN: Xiaomi-Kamera -> Gemini Vision (Kernvision, Bausteine da)
- PROAKTIV: JACK meldet sich von selbst (Watchdog schreibt dir)
- SELBSTVERBESSERUNG: JACK liest eigenen Code -> Patch-Vorschlag -> deine Freigabe -> Selbstumbau + Commit
- OFFLINE-HIRN: 7B+ Modell wenn bessere Hardware da
