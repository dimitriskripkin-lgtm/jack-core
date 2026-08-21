"""P2 Memory-Pruning: Alte Einträge komprimieren (Qwen 21.08.)
Läuft einmal am Tag, löscht alte memory-Einträge, markiert ingested als stale."""
import sqlite3, os, datetime

J = os.path.expanduser("~/jack")
MEMORY_DB = os.path.join(J, "jack_memory.db")

def prune_memory(days_old=30):
    """Löscht memory-Einträge älter als X Tage."""
    try:
        con = sqlite3.connect(MEMORY_DB, timeout=10)
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=days_old)).isoformat()
        
        # Zähle vor dem Löschen
        before = con.execute("SELECT COUNT(*) FROM memory").fetchone()[0]
        
        # Lösche alte Einträge (nicht in Episoden referenziert, keine Kinder)
        con.execute("""
            DELETE FROM memory
            WHERE time < ?
            AND parent_id IS NULL
        """, (cutoff,))
        
        con.commit()
        after = con.execute("SELECT COUNT(*) FROM memory").fetchone()[0]
        con.close()
        
        return f"MEMORY: {before} -> {after} ({before - after} gelöscht, cutoff={cutoff[:10]})"
    except Exception as e:
        return f"MEMORY-FEHLER: {e}"

def prune_ingested(max_entries=10000):
    """Markiert alte ingested_context als stale, löscht wenn > max_entries."""
    try:
        con = sqlite3.connect(MEMORY_DB, timeout=10)
        
        before = con.execute("SELECT COUNT(*) FROM ingested_context").fetchone()[0]
        
        if before > max_entries:
            # Lösche älteste 20%
            cutoff_id = con.execute("""
                SELECT id FROM ingested_context
                ORDER BY created_at ASC
                LIMIT ?
            """, (before // 5,)).fetchall()
            
            if cutoff_id:
                ids = [row[0] for row in cutoff_id]
                con.execute(f"DELETE FROM ingested_context WHERE id IN ({','.join(map(str, ids))})")
        
        con.commit()
        after = con.execute("SELECT COUNT(*) FROM ingested_context").fetchone()[0]
        con.close()
        
        return f"INGESTED: {before} -> {after} ({before - after} gelöscht)"
    except Exception as e:
        return f"INGESTED-FEHLER: {e}"

def run():
    """Hauptfunktion: Pruning für alle Tabellen."""
    results = []
    results.append(prune_memory(30))
    results.append(prune_ingested(10000))
    return " | ".join(results)

if __name__ == "__main__":
    print(run())
