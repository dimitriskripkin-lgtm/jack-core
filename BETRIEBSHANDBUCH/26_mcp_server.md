# 26. jack_mcp_server.py

Gelesen 03.10.2026, erste 55 Zeilen. Kein Umbau.

**Zweck:** Tuer fuer externe KIs. FastMCP, Port 8000.

**Auth:** Token aus .jack_mcp_token, Zeile JACK_MCP_TOKEN. Fehlt die Datei oder ist der Wert leer, laesst die Middleware jeden durch. Mit Token nur Bearer, sonst 401.

**Daten:** graph_list_nodes und graph_read_node lesen jack_graph.db. Memory-DB ist importiert.

**Offen:** Bind-Adresse und Act-Liste hinter dem Schnitt nicht zitiert.
