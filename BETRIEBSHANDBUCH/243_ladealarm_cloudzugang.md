# 243 Lade-Alarm (08.10.2026, Dima: Punkt 2) und Cloud-Token-Weg
## Lade-Alarm (JACK_TUNE_LADEALARM, jack_autonomous._proaktiv_loop)
Honor-Akku unter 40 % und nicht ladend: einmalige Vorwarnung "erst ans Ladegeraet" (max. alle 6 h). Unter 20 %: bisherige Warnung, aber Takt 10 Min statt 30. Quelle jack_health_now.json (max 15 Min alt). Grenze: ein Alarm laedt kein Handy; wenn niemand da ist (Nachtschicht), hilft nur die Vorwarnung vor dem Losfahren.
## Token fuer Cloud-Nachtlauf
Token liegt nur in ~/jack/.jack_mcp_token (nie ausgeben). Dima kopiert ihn per termux-clipboard-set in die Zwischenablage (ohne Anzeige) und traegt ihn im claude.ai/code Cloud-Environment als Variable JACK_MCP_TOKEN ein (plus JACK_MCP_URL). Netzwerk-Allowlist des Environments muss mcp.jack-mcp-cloudflare.bid und github.com erlauben.
