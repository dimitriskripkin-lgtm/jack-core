## 8. jack_intent.py (385 Zeilen, Autonomie-Level-System)

**Zweck:** Erkennt aus Freitext eine konkrete Absicht ("Aktion") und entscheidet anhand eines
**numerischen Autonomie-Levels (1-4)**, ob JACK selbst handelt oder erst nachfragt. Das ist die
reale Umsetzung der schon in den ältesten Projektnotizen genannten Regel "Kein Autonomie-Level
erfinden" — hier ist das Level KEINE Erfindung einer KI-Session, sondern ein echtes, gespeichertes
Setting (`get_level()`/`set_level()`), das offenbar bewusst von Dima eingeführt wurde.

**Sechstes gefundenes Gate, anders als die vorherigen fünf.** Kapitel 1/2/5 beschreiben fünf
Ja/Nein-Freigaben für JEWEILS EINEN konkreten, schon formulierten Vorschlag. Dieses System hier ist
grundsätzlich anders: ein **globaler Zahlenregler** pro Session, der für JEDE erkannte Absicht
gilt, abgestuft nach Vertrauen (`confidence`) und einer pro Aktionstyp hinterlegten Mindeststufe
(`AKTIONEN`-Tabelle, noch nicht im Detail gelesen welche Aktionen welche Stufe brauchen).

**`detect(text)` — Ablauf:**
1. **Zuerst** `jack_exec.handle_ui_intent(text)` — falls das greift, läuft es sofort durch
   (`level_ok: True`, `ausgefuehrt: True`), **ohne** die Level-Logik überhaupt zu befragen.
   Kommentar im Code nennt das "UI_INTENT_GATE: gleiche Leitung wie Voice/Telegram/exec" — ein
   gemeinsamer Eingang für mehrere Aufrufer, noch nicht im Detail geklärt welche.
2. Sonst: `_keyword_detect()`, bei Unschärfe zusätzlich `_gemini_detect()` als Fallback.
3. Level-Logik: bei Level ≥4 handelt JACK ab Konfidenz 0,6 praktisch immer selbst; bei Level 2-3
   nur wenn die Mindeststufe der Aktion erreicht ist, sonst Rückfrage; niedrigere Level fragen fast
   immer nach.

**Aufgelöster Widerspruch aus der alten Modulkarte:** Die Behauptung "Xiaomi-IP ist immer
10.58.220.131" war nie korrekt haltbar — `execute()`/`_ssh()` lesen die IP zur Laufzeit aus
`jack_config.get_param('NETWORK', 'xiaomi_ip')`. Die IP ist eine Konfigurationseinstellung, keine
Konstante; sie ändert sich real (vermutlich DHCP), die SSH-Timeouts vom 02.10. mit einer anderen
IP waren also kein Fehler, sondern der Normalfall nach einem IP-Wechsel.

**`muster_analyse()`** — wertet die Intent-Historie (eigene kleine DB, `_init_db()`) aus, vermutlich
um zu erkennen, welche Absichten häufig falsch erkannt werden (noch nicht im Detail gelesen).

**Offene Fragen für später:** Welche Aktionen stehen in der `AKTIONEN`-Tabelle, und welche
Mindeststufe haben sie? Was genau ist `jack_exec.handle_ui_intent()`, und wer ruft `jack_intent.detect()`
tatsächlich auf (noch nicht geprüft, ob `jack_telegram.py` oder ein Voice-Pfad das nutzt)?
