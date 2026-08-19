#!/usr/bin/env python3
"""
Phase 8: Intent-Katalog-Parser
Extrahiert Intent-Filter aus dumpsys package Resolver Tables.
"""
import sqlite3, re, os

DUMP_FILE = os.path.expanduser("~/jack/xiaomi_dumpsys_package.txt")
DB_FILE = os.path.expanduser("~/jack/jack_cmd_crawler.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS intents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resolver_type TEXT NOT NULL,
            action TEXT,
            mime_type TEXT,
            package TEXT,
            component TEXT,
            hash_id TEXT,
            UNIQUE(resolver_type, mime_type, package, component)
        )
    """)
    return conn

def parse_resolver_table(lines, start_idx, resolver_type):
    """Parst eine Resolver Table und extrahiert Action→MIME→Komponente"""
    intents = []
    i = start_idx
    
    # Suche nach "Full MIME Types:" oder direkt nach MIME-Types
    while i < len(lines) and not lines[i].strip().startswith("Full MIME Types:"):
        i += 1
    
    if i >= len(lines):
        return intents
    
    i += 1  # Skip "Full MIME Types:"
    
    current_mime = None
    
    while i < len(lines):
        line = lines[i]
        
        # Ende der Table (nächste Table oder leerer Block)
        if line.strip() and not line.startswith(" ") and ":" in line:
            break
        
        # MIME-Type (z.B. "text/comma-separated-values:")
        mime_match = re.match(r'^\s+(\S+):\s*$', line)
        if mime_match:
            current_mime = mime_match.group(1)
            i += 1
            continue
        
        # Komponenten-Eintrag (z.B. "17bf830 com.google.android.apps.bard/.shellapp.BardEntryPointActivity")
        if current_mime:
            comp_match = re.match(r'^\s+([0-9a-f]+)\s+(\S+)/(\S+)\s*$', line)
            if comp_match:
                hash_id = comp_match.group(1)
                package = comp_match.group(2)
                component = comp_match.group(3)
                intents.append({
                    'resolver_type': resolver_type,
                    'action': 'android.intent.action.VIEW',  # Standard für MIME
                    'mime_type': current_mime,
                    'package': package,
                    'component': component,
                    'hash_id': hash_id
                })
        
        i += 1
    
    return intents

def main():
    print("=== Phase 8: Intent-Katalog-Parser ===")
    print(f"Lese {DUMP_FILE}...")
    
    with open(DUMP_FILE, encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    print(f"✓ {len(lines)} Zeilen geladen")
    
    # Finde die 4 Resolver Tables
    tables = {
        'Activity': None,
        'Receiver': None,
        'Service': None,
        'Provider': None
    }
    
    for i, line in enumerate(lines):
        if 'Activity Resolver Table:' in line:
            tables['Activity'] = i
        elif 'Receiver Resolver Table:' in line:
            tables['Receiver'] = i
        elif 'Service Resolver Table:' in line:
            tables['Service'] = i
        elif 'Provider Resolver Table:' in line:
            tables['Provider'] = i
    
    print(f"✓ Resolver Tables gefunden:")
    for name, idx in tables.items():
        if idx is not None:
            print(f"  {name}: Zeile {idx+1}")
    
    # DB initialisieren
    conn = init_db()
    
    # Alle Tables parsen
    total_intents = 0
    for resolver_type, start_idx in tables.items():
        if start_idx is None:
            continue
        
        print(f"\nParse {resolver_type} Resolver Table...")
        intents = parse_resolver_table(lines, start_idx, resolver_type)
        
        # In DB schreiben (INSERT OR IGNORE für Duplikate)
        inserted = 0
        for intent in intents:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO intents 
                    (resolver_type, action, mime_type, package, component, hash_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    intent['resolver_type'],
                    intent['action'],
                    intent['mime_type'],
                    intent['package'],
                    intent['component'],
                    intent['hash_id']
                ))
                if conn.total_changes > inserted:
                    inserted += 1
            except sqlite3.Error as e:
                print(f"  ⚠ DB-Fehler: {e}")
        
        conn.commit()
        print(f"  → {len(intents)} Einträge gefunden, {inserted} neu eingefügt")
        total_intents += inserted
    
    print(f"\n=== Statistik ===")
    stats = conn.execute("""
        SELECT resolver_type, COUNT(*) 
        FROM intents 
        GROUP BY resolver_type
    """).fetchall()
    
    for resolver_type, count in stats:
        print(f"  {resolver_type}: {count} Intents")
    
    total = conn.execute("SELECT COUNT(*) FROM intents").fetchone()[0]
    print(f"\n✓ Gesamt: {total} Intent-Einträge in DB")
    
    conn.close()

if __name__ == "__main__":
    main()
