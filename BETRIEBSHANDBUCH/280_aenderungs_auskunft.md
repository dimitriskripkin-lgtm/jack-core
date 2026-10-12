# 280 - jack_aenderung.py (Aenderungs-Auskunft)

Stand 12.10.2026. Deterministisch, kein LLM. Beantwortet "Was hat sich geaendert / ist neu / lief" aus dem git-Verlauf.

## Wo es haengt
- `jack_chat_router.py`: `classify()` ruft `jack_aenderung.erkennt(text)`; Treffer -> Spur NEU. `dispatch()` und `dispatch_lane()` rufen bei NEU `neu_antwort(text)`: erst `jack_aenderung.antwort(text)`, sonst der alte `neu_report(10)` (feste 10 Std). Keine neue Spur (jack_telegram.py kennt NEU schon).
- Marker: JACK_TUNE_AENDERUNG.

## Regeln (vorregistriert, ARBEITSPLATZ/gemeinsam/arena/talk_vorregistrierung.md)
- Fenster relativ zum Aufrufzeitpunkt (lokale Zeit): letzte N Stunden/Tage exakt, heute ab 00:00, gestern/vorgestern als Tagesfenster, "seit gestern/vorgestern/<Wochentag>" ab 00:00, diese Woche ab Montag.
- Standardfenster (kuerzlich/neulich/zuletzt oder nur Thema) = 96 Stunden (= Evidenzfenster der Arena-Probe; urspruenglich 7 Tage, nach Uebungsbefund gesenkt).
- Themenfilter: Begriffe >= 4 Zeichen nach Stoppwoertern, gegen Commit-Betreff + Dateinamen; nur Commits mit der hoechsten Begriffs-Trefferzahl.
- Nur die erste Teilfrage (vor ", und wie/wer/..." ) bestimmt Fenster und Thema; gibt es eine zweite, haengt "Zum Rest der Frage habe ich keine belegten Angaben." an.
- Kein Treffer: "Dazu habe ich keine passenden Aenderungen im git-Verlauf gefunden." Nie Ersatz aus Graph/Memory.
- Ausgabe: bis 8 Commits, Zeit in Alltagsworten (heute nachmittag, gestern abend, Wochentag, vor N Tagen), kein Kalenderdatum, keine Uhrzeit. Commit-Zahl im Kopf nur bei reinem Zeitfenster.

## Warum so (Uebungsbefunde, Richter v6 unveraendert, Fingerprint 85e1715182c7e592)
- Kalenderdaten/Uhrzeiten kann der Anker nicht pruefen -> JUDGE_ERROR; deshalb Tageswort + Tagesteil.
- Commit-Zahlen prueft der Anker nur fuer Zeitfenster -> bei Standardfenster/Thema keine Zahl im Kopf.
- Verneinungssatz ohne Ziffern und ohne Klammerdetail, sonst splittet der Claim-Extraktor ihn und labelt das Thema als ERFUNDEN.

## Messung (nur Uebungssatz fragen_uebung.json, Hash 38a23ede5e6d6c80)
- Basis alt (basis_uebung_20261012c): 28 gewertet, PASS 10 (alle 10 Unbekannt-Faelle), missed_available 16, fabrication 2.
- Neu, letzter Entwicklungslauf (neu_uebung_20261012e): 27 gewertet, PASS 26, missed_available 0, misrepresented 0, fabrication 1 (U28, danach behoben, Teiltest neu_neg_20261012a 2/2), JUDGE_ERROR 3.
- Das ist Entwicklung, KEINE Abnahme. Abnahme nur ueber den versiegelten Holdout, genau einmal, mit Dimas Go, beide Arme (alt/neu) auf demselben eingefrorenen Snapshot. Tor: fabrication und misrepresented duerfen nicht steigen, missed_available muss klar sinken, Unbekannt-Faelle nicht schlechter.

## Offen
- Live-Dienst jack_telegram muss neu gestartet werden, damit die Auskunft im echten Chat greift.
- Holdout-Lauf (alt/neu) steht aus.
- LLM-Pfad (nicht Aenderungsfrage) bleibt unveraendert: U09 "Phone-Sinne" erfindet weiter (auch in der Basis).
- Fenster ueber 96 Std liegen ausserhalb der Probe-Evidenz, nicht messbar.
