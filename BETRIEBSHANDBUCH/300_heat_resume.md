# 300 HEATRESUME: Autolearn nach Hitzestopp zurueck (22.10.2026)

Symptom: jack_autolearn stand stundenlang still (21.10. ab 13:15, frueher 10.10. 11:32/16:50, Kap 272 'wer stoppt?').
Ursache (gemessen): jack_cortex ruft jack_heat_protection.emergency_stop() auf. Ab 65 C (thermal_zone0) -> sv stop jack_autolearn, ohne Rueckweg. Wiederbelebung nur ueber Waechter _heartbeat_sv_check nach 22000 s Herzschlag-Alter (~6 h). Beleg Telemetrie 21.10.: 13:10 39,7 C, 13:15 68,7 C, 13:20 39,6 C; Autolearn wieder an ~19:15. Der Waechter-Thread _autolearn_loop ist tot (D2ONE), kein Doppelbetrieb.
Fix (JACK_TUNE_HEATRESUME):
- jack_heat_protection.emergency_stop: nach sv stop Marke ~/jack/.heat_paused_autolearn (Zeitstempel).
- jack_autonomous._heartbeat_sv_check (Anfang): Marke da und Honor 0 < t < HONOR_TEMP_WARN (55) -> sv start jack_autolearn, Marke weg, notify(wichtig=False). Fehler -> Marke weg (alter 6-h-Weg bleibt), notify sichtbar.
Notbremse selbst unveraendert. Backups *.bak_20261022_heat. Neustart jack_cortex + jack_waechter 22.10. 01:34.
Test: Marke von Hand gesetzt (Honor 32 C), Waechter-Runde muss sie entfernen.
Offen: Quelle der Hitzespitze 21.10. 13:15 unbekannt.
Nachweis 22.10. 01:36 (LIVE): Waechter entfernte die Test-Marke in seiner ersten Runde nach Neustart, Honor 37 C. Meldung lief mit wichtig=False in den Fahrpuffer (logs/telegram_fahrt_queue.jsonl, status GEPUFFERT, Fahrmodus MBUX 33188). Damit auch erster echter Puffer-Eintrag von Kap 299.
