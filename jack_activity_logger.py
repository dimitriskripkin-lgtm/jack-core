"""Activity-Logger: Xiaomi + Roller Events loggen (Qwen 21.08.)
Loggt Screen-Wechsel, OBD2-Daten, generiert Zusammenfassungen."""
import sqlite3, os, datetime

J = os.path.expanduser("~/jack")
MEMORY_DB = os.path.join(J, "jack_memory.db")

def log_event(device, event_type, details="", summary=""):
    """Loggt ein Event in activity_log."""
    try:
        con = sqlite3.connect(MEMORY_DB, timeout=5)
        con.execute("""
            INSERT INTO activity_log (ts, device, event_type, details, summary)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.datetime.now().isoformat(),
            device,
            event_type,
            details[:500] if details else "",
            summary[:1000] if summary else ""
        ))
        con.commit()
        con.close()
        return True
    except Exception as e:
        return False

def get_recent(device=None, hours=24, limit=50):
    """Holt letzte Events."""
    try:
        con = sqlite3.connect(MEMORY_DB, timeout=5)
        cutoff = (datetime.datetime.now() - datetime.timedelta(hours=hours)).isoformat()
        
        if device:
            rows = con.execute("""
                SELECT ts, device, event_type, details, summary
                FROM activity_log
                WHERE ts > ? AND device = ?
                ORDER BY ts DESC
                LIMIT ?
            """, (cutoff, device, limit)).fetchall()
        else:
            rows = con.execute("""
                SELECT ts, device, event_type, details, summary
                FROM activity_log
                WHERE ts > ?
                ORDER BY ts DESC
                LIMIT ?
            """, (cutoff, limit)).fetchall()
        
        con.close()
        return rows
    except Exception:
        return []

def generate_summary(hours=24):
    """Generiert Zusammenfassung der letzten X Stunden."""
    events = get_recent(hours=hours)
    if not events:
        return "Keine Aktivitäten in den letzten 24h."
    
    by_device = {}
    for ts, device, etype, details, summary in events:
        if device not in by_device:
            by_device[device] = []
        by_device[device].append((ts, etype, details))
    
    lines = [f"AKTIVITÄTEN (letzte {hours}h):"]
    for device, evts in by_device.items():
        lines.append(f"\n{device.upper()}: {len(evts)} Events")
        for ts, etype, details in evts[:10]:
            lines.append(f"  {ts[11:16]} {etype}: {details[:60]}")
        if len(evts) > 10:
            lines.append(f"  ... +{len(evts)-10} weitere")
    
    return "\n".join(lines)

def log_xiaomi_screen_change(old_pkg, new_pkg):
    """Wird von jack_focus_monitor aufgerufen."""
    log_event("xiaomi", "screen_change", f"{old_pkg} -> {new_pkg}")

def log_obd2_data(data_dict):
    """Loggt OBD2-Daten wenn Adapter da ist."""
    details = ", ".join(f"{k}={v}" for k, v in data_dict.items())
    log_event("roller", "obd2", details)
