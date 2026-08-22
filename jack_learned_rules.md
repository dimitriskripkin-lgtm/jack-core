# GELERNTE REGELN (automatisch aus Fehlern)

Stand: 21.08.2026 07:40

Keine offenen Fehler - keine Regeln gelernt.

## [22.08.2026] HITZE-VORFALL: Shadow-Fixer Endlosschleife
**Vorfall:** Shadow-Fixer wird von jack_autonomous.py (Waechter) periodisch aufgerufen. Wenn Patch-Versuche scheitern, lädt der Shadow-Fixer llama3.2:3b für jeden Versuch. Der Waechter ruft ihn alle paar Minuten auf → Endlosschleife → 94°C CPU, 172MB RAM frei, JACK tot.

**REGEL:**
1. **Shadow-Fixer + lokales LLM = Hitze-Falle.** Jeder Patch-Versuch lädt das Modell. Wenn Patch-Versuche 3x scheitern, MUSS der Shadow-Fixer deaktiviert werden.
2. **Endlosschleifen können in der AUFRUFSCHLEIFE sitzen, nicht im aufgerufenen Code.** jack_autofixer_shadow.py hat KEINEN Loop — die Loop ist in jack_autonomous.py (Waechter) der ihn periodisch aufruft.
3. **Heat-Protection muss im AUFRUFER sitzen** (Waechter), nicht im aufgerufenen Modul (Shadow-Fixer).
4. **3-Stufen Heat-Protection:** Warnung (55°C), Blockade (65°C), Notfall (75°C).
5. **Vor dem Patchen IMMER die Aufrufkette verstehen:** grep "shadow\|autofixer" jack_autonomous.py → Zeile 160-165 zeigt den Call.

**Vermeidung:**
- Shadow-Fixer nur bei CPU < 55°C aufrufen
- Nach 3x gescheiterten Patch-Versuchen: Shadow-Fixer deaktivieren, nicht wiederholen
- Waechter (jack_autonomous.py) alle 30 Minuten neu starten
- llama-server NICHT automatisch neu starten wenn CPU > 55°C
