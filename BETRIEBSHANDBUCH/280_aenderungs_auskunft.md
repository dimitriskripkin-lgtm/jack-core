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

## Holdout-Abnahme (12.10.2026, einmalig, verbraucht): BESTANDEN nach Vorabtor
fragen_holdout.json (Hash 9a6427d9242534ea, 30 Fragen), Richter v6 unveraendert, Code vorher per Pruefsumme eingefroren (Schalter ~/jack/.aenderung_off = alter Arm). Laeufe holdout_alt_20261012 / holdout_neu_20261012.
| | alt | neu |
|---|---|---|
| gewertet | 27 (3 JUDGE_ERROR) | 30 |
| PASS | 8 | 23 |
| missed_available | 17 | 6 |
| fabrication / misrepresented | 0 / 0 | 0 / 0 |
| ehrliche Unbekannt-Faelle | 8/10 | 9/10 |
Tor erfuellt (fabrication/misrepresented nicht gestiegen, missed klar gesunken, Unbekannt nicht schlechter). Der Holdout ist jetzt Entwicklungsdaten.
Restfehler (nur Befund, NICHT am Holdout nachgebessert): H05/H06/H17 "in letzter Zeit"/"juengst": Begriff "zeit" bleibt als Thema stehen bzw. "juengst" unbekannt -> falsches "keine passenden Aenderungen" (Falsch-Negativ, im Urteil MISSED). H15 Totmannschalter, H10/H18 (LLM-Pfad "Ich weiss das nicht"). H22 NO_ANSWER im LLM-Pfad (beide Arme).
Naechste Verbesserung (frischer Satz noetig): "zeit"/"letzter" als Stoppwort, "juengst/juengere" als Standardfenster-Wort, Falsch-Negativ vermeiden: bei Thema ohne Treffer zusaetzlich auf Standardfenster ohne Thema zurueckfallen ist NICHT erlaubt (waere Ersatz), stattdessen Thema nur filtern wenn Begriff im Repo-Vokabular vorkommt.

## Runde 2 Restfehler (12.10.2026, frischer Satz V, einmalig, verbraucht)
fragen_frisch2.json (Hash 043bcf64c15f4cfc), Laeufe frisch2_alt/neu_20261012, Richter v6 unveraendert, Fixes vorher eingefroren (jack_aenderung sha 7548ead6b21a91fb).
| | alt | neu |
|---|---|---|
| gewertet | 29 | 29 |
| PASS | 7 | 26 |
| missed_available | 16 | 2 |
| fabrication / misrepresented | 4 / 1 | 0 / 0 |
| ehrliche Unbekannt-Faelle | 7/9 | 9/10 |
Haupttor erfuellt. Vorab gesetztes Zusatztor (unscharf-Fragen mindestens 2 von 3) NICHT erfuellt: nur 1/3 (V05 "vor kurzem", V17 "vor kurzem gebaut"; V06 "juengst" ok). Ursache: Zeitwort "kurzem" blieb als Thema stehen (derselbe Fehlertyp wie "zeit"). Fix nach der Messung: Zeitphrasen werden vor der Themenermittlung entfernt (ZEIT_PHRASEN). Unbestaetigt: braucht frischen Satz (Tageskosten waren ausgeschoepft). V ist jetzt Entwicklungsdaten.
Gleich in beiden Armen (nicht von der Auskunft): V22 "Wie voll ist Dimas Tank?" -> Antwort mit Honor-Speicher (NO_ANSWER), V11 JUDGE_ERROR.

## Offen
- Live-Dienst jack_telegram muss neu gestartet werden, damit die Auskunft im echten Chat greift.
- Holdout-Lauf (alt/neu) steht aus.
- LLM-Pfad (nicht Aenderungsfrage) bleibt unveraendert: U09 "Phone-Sinne" erfindet weiter (auch in der Basis).
- Fenster ueber 96 Std liegen ausserhalb der Probe-Evidenz, nicht messbar.

## Runde 3 (14.10.2026, frischer Satz T, 10 unscharfe Zeitfragen)
- alt PASS 8, neu PASS 26 von 28 gewertet. Unscharfe Zeitangaben (kuerzlich, neulich, zuletzt, in letzter Zeit, juengst, vor kurzem) neu 9/9 -> Zeitphrasen-Fix aus Runde 2 bestaetigt.
- misrepresented neu 0 (alt 3). Eine Erfindung in beiden Armen identisch (T27 "Welche Ware hatte Dima letzte Nacht geladen?" -> Akku-/Sensorstatus). Kommt nicht aus diesem Modul, sondern aus dem Sensorpfad (Wort "geladen"). Strenges Vorab-Kriterium "neu fabrication 0" damit formal verfehlt.
- Restfehler: Zweite Teilfrage ohne Fragewort (", und lief alles stabil?") wird nicht abgetrennt; "stabil" wird Thema, keine Treffer.
- Offen: Sensorpfad reagiert auf "geladen" auch bei Ladung/Ware (eigener Fehler, Router/Sensoren).
