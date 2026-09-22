#!/usr/bin/env python3
"""Qwen-Client — sammelt periodisch JACK-Daten für externe KI"""
import asyncio
import json
import os
from datetime import datetime
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

MCP_URL = "http://localhost:8000/mcp"
OUTPUT_FILE = "/data/data/com.termux/files/home/jack/qwen_snapshot.json"

async def collect_snapshot():
    """Sammelt Graph, Memory und Status für Qwen"""
    try:
        async with streamable_http_client(MCP_URL) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Graph: letzte 10 Knoten
                graph_result = await session.call_tool("graph_list_nodes", {"limit": 10})
                graph_data = json.loads(graph_result.content[0].text)
                
                # Memory: letzte 5 Einträge
                memory_result = await session.call_tool("memory_recent", {"limit": 5})
                memory_data = json.loads(memory_result.content[0].text)
                
                # Mission-Ergebnisse
                mission_result = await session.call_tool("memory_search", {"query": "mission_result", "limit": 3})
                mission_data = json.loads(mission_result.content[0].text)
                
                snapshot = {
                    "timestamp": datetime.now().isoformat(),
                    "graph": graph_data,
                    "memory": memory_data,
                    "missions": mission_data
                }
                
                # In Datei speichern
                with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                    json.dump(snapshot, f, ensure_ascii=False, indent=2)
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Snapshot gespeichert: {OUTPUT_FILE}")
                return True
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Fehler: {e}")
        return False

async def main():
    """Läuft periodisch alle 5 Minuten"""
    print(f"Qwen-Client gestartet, sammelt alle 5 Minuten nach {OUTPUT_FILE}")
    while True:
        await collect_snapshot()
        await asyncio.sleep(300)  # 5 Minuten

if __name__ == "__main__":
    asyncio.run(main())
