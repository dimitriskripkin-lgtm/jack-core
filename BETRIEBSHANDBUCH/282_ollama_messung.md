# 282 Ollama-Messung 13.10.2026 und Modelle geloescht

Entscheidung Dima 13.10.2026 17:47: Modelle loeschen, lokale Modelle kommen mit staerkerer Hardware zurueck. Politik vom 28.09. gilt weiter (Ollama Standard AUS, .ollama_lock gesetzt).

## Messung (Xiaomi, Sitzung per xiaomi_ollama_restart, danach xiaomi_ollama_stop)
- Embeddings nomic-embed-text: 281 Kapitel in 756 s (2,7 s/Kapitel). 8 Synonymfragen (Hitzeschutz, Fokus, Kortex ...): richtiges Kapitel 0/8 auf Rang 1, 0/8 in Top 3 (Raenge 40-275). Als Suchhilfe unbrauchbar.
- Text llama3.2:3b: 1,6 Tokens/s, 165 s fuer eine Antwort. qwen3:4b nicht mehr gemessen (Abbruch wegen Waerme/Zeit).
- Temperatur: thermal_zone0 31-36 Grad, CPU-Kerne unter Last 49-65 Grad. RAM frei ca. 3,2 GB von 7,2 GB.

## Geloescht 13.10.2026
- Honor ~/.ollama/models (llama3.2 3b, moondream, nomic-embed-text): 3,8 GB -> 27 KB.
- Xiaomi ~/.ollama/models (qwen3:4b, llama3.2:3b, nomic-embed-text): 4,5 GB -> 23 KB.
- Dienste und Binaries unveraendert.

## Abhaengigkeiten (gelesen 14.10.)
- jack_talk.py: MODEL_NAME qwen3:4b (Chat) und nomic-embed-text (get_embedding). Beide Pfade pruefen zuerst .ollama_lock und geben dann None zurueck. Solange der Lock steht: keine Wirkung.
- jack_lokal.py (llama3.2:3b, qwen2.5:3b, phi3), jack_ollama_gate.py (llama3.2:3b Standard).
- WICHTIG: Wer den Lock aufhebt, muss vorher ein Modell ziehen (ollama pull), sonst laufen diese Pfade in Fehler.
