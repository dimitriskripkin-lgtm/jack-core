# 291 Architekturentscheidung: Intent zuerst, UI zuletzt (21.10.2026)

Entschieden von Dima, 21.10.2026 ca. 05:10, im Gespraech mit Claude.

## Ausgangslage
Eine Woche lang wurden Arena E (Einstellungen lesen: Android-Version, Modell, MIUI, Speicher, Akku, Sprache), Haende B (mobile-use) und der Wegbuch-Lehrer (Auftrag 17) auf genau diese Lesewege getrimmt. Ergebnis: Eigener Actor A 37,5 %, Haende B 3/9 bei ca. 18-fachen Kosten, viel Aufwand fuer Skills ohne Nutzen. Den Akku sieht Dima mit einem Blick, JACK fragt ihn ohnehin per Shell ab.

## Erkenntnis
Die Einstellungen waren als Pruefstand gedacht (harmlos, unabhaengiges Orakel vorhanden) und sind unbemerkt zum Ziel geworden. Fehler von Claude. UI-Automation ist branchenweit die unzuverlaessigste Schicht und darf nur der Rest sein.

## Entscheidung: Reihenfolge pro Skill
1. Intent / Deep-Link (am start -a ..., URL-Schema): ein Befehl, deterministisch, 0 Cent. Beispiele: Timer, Wecker, Maps-Navigation, Websuche, Link oeffnen, Teilen, Kamera, Kalendereintrag, Einstellungsseite direkt.
2. Root-Shell auf dem Xiaomi (settings, dumpsys, cmd, input keyevent fuer Medien): kein Bildschirm noetig.
3. UI (tippen, wischen, Bildschirm lesen) nur fuer den Rest. Dann: Claude faehrt als Lehrer vor (Mechanik aus Auftrag 17, App-Liste auf die Ziel-Skills erweitert, Nie-Liste bleibt), Dima bestaetigt ja/nein, Wegbuch spielt den Weg danach gratis ab.

## Skill-Liste
Statt Einstellungen eine Liste mit ca. 20 nuetzlichen und vorzeigbaren Skills, pro Skill markiert: Intent / Shell / UI. Quellen: Tasker-, MacroDroid-, Automate-Rezepte (fast alle intent-basiert), Datensaetze wie Google Android in the Wild (715k Ablaeufe, 30k Anweisungen) nur als Ideen- und Haeufigkeitsquelle, nicht zum Abspielen.

## Status der betroffenen Arbeiten
- Auftrag 17 (Wegbuch-Lehrer): fertig, Review mit 2 Fixes (force-stop vor Start, nur Skill 1-6), offline 26/26 und Patch-Vertrag 6/6 gruen. GEPARKT, nicht eingebaut. Wird spaeter mit erweiterter App-Liste fuer Stufe 3 wiederverwendet.
- Auftrag 18 (Finger-Vormachen): PAUSIERT.
- Arena: erst wieder, wenn echte Skills verdrahtet sind. Intent-Skills brauchen keinen 3-fach-Lauf.

## Arbeitsregel
Erst reden, dann bauen: Richtungswechsel werden mit Dima besprochen, bevor eine Woche entwickelt wird. Pruefstand nie mit Ziel verwechseln.
