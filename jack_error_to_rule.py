"""P1 Error-to-Rule: Fehler aus jack_errors.db werden zu harten Regeln.
Qwen 21.08. - lernt aus jedem Fehler, schreibt nach jack_learned_rules.md"""
import sqlite3, os, json, datetime

J = os.path.expanduser("~/jack")
ERRORS_DB = os.path.join(J, "jack_errors.db")
RULES_MD = os.path.join(J, "jack_learned_rules.md")
RULES_JSON = os.path.join(J, "jack_learned_rules.json")

# Pattern: error_type + Stichwort -> Regel
PATTERNS = {
    ("CORTEX_ERR", "SSH"): "SSH-Befehle NUR mit Timeout und via su -c. Kein /tmp nutzen.",
    ("CORTEX_ERR", "Timeout"): "Bei Timeout: ControlMaster pruefen, dann Wake-Lock auf Xiaomi.",
    ("LOGGED_ERR", "Kanaltest"): "Test-Fehler ignorieren, nicht als echte Fehler behandeln.",
    ("LOGGED_ERR", "Lasttest"): "Test-Fehler ignorieren, nicht als echte Fehler behandeln.",
    ("MODULE_ERR", "import"): "Vor JEDEM Import: try/except mit Fallback. Module koennen fehlen.",
    ("MODULE_ERR", "No module"): "Fehlendes Modul: pkg install oder pip install --break-system-packages.",
    ("EXEC_ERR", "monkey"): "Monkey braucht entsperrten Screen. jack_xiaomi_unlock.ensure_unlocked() vorher aufrufen.",
    ("EXEC_ERR", "Permission"): "Permission-Fehler: su -c nutzen oder AppOps pruefen.",
    ("EXEC_ERR", "not found"): "Befehl nicht gefunden: Pfad pruefen, $PREFIX/tmp statt /tmp.",
    ("EXEC_ERR", "rc=1"): "rc=1 bedeutet Fehler. NICHT als Erfolg behandeln.",
    ("EXEC_ERR", "rc=255"): "rc=255 bedeutet Usage-Text (Android-Konvention). Befehl ist falsch.",
    ("LLM_ERR", "halluz"): "LLM halluziniert: KEINE SSH-Syntax erfinden, monkey+App-Map nutzen.",
    ("LLM_ERR", "Timeout"): "LLM-Timeout: Modell wechseln oder Prompt kuerzen.",
    ("TG_ERR", "send"): "Telegram-Send-Fehler: Chat-ID pruefen, Token rotieren.",
    ("TG_ERR", "keyboard"): "Keyboard-Fehler: Inline-Button Format pruefen.",
}

def lade_fehler(limit=50):
    try:
        con = sqlite3.connect(ERRORS_DB, timeout=5)
        rows = con.execute("""
            SELECT module, error_type, error_msg, COUNT(*) as anzahl
            FROM errors
            WHERE resolved=0
            GROUP BY module, error_type, error_msg
            ORDER BY anzahl DESC
            LIMIT ?
        """, (limit,)).fetchall()
        con.close()
        return rows
    except Exception as e:
        return []

def generiere_regeln(fehler):
    regeln = []
    for module, etype, msg, anzahl in fehler:
        matched = False
        for (pat_type, pat_kw), regel in PATTERNS.items():
            if pat_type in str(etype) and pat_kw.lower() in str(msg).lower():
                regeln.append({
                    "quelle": f"{module}/{etype}",
                    "fehler": msg[:80],
                    "regel": regel,
                    "anzahl": anzahl,
                    "ts": datetime.datetime.now().isoformat()
                })
                matched = True
                break
        if not matched and anzahl >= 2:
            regeln.append({
                "quelle": f"{module}/{etype}",
                "fehler": msg[:80],
                "regel": f"WIEDERKEHRENDER FEHLER ({anzahl}x): {msg[:60]} - Ursache pruefen.",
                "anzahl": anzahl,
                "ts": datetime.datetime.now().isoformat()
            })
    return regeln

def schreibe_regeln(regeln):
    with open(RULES_JSON, "w", encoding="utf-8") as f:
        json.dump(regeln, f, indent=2, ensure_ascii=False)
    with open(RULES_MD, "w", encoding="utf-8") as f:
        f.write("# GELERNTE REGELN (automatisch aus Fehlern)\n\n")
        f.write(f"Stand: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n")
        if not regeln:
            f.write("Keine offenen Fehler - keine Regeln gelernt.\n")
        else:
            for r in regeln:
                f.write(f"## [{r['anzahl']}x] {r['quelle']}\n")
                f.write(f"Fehler: {r['fehler']}\n")
                f.write(f"**REGEL: {r['regel']}**\n\n")
    return len(regeln)

def run():
    fehler = lade_fehler()
    regeln = generiere_regeln(fehler)
    n = schreibe_regeln(regeln)
    return f"ERROR-TO-RULE: {len(fehler)} Fehler analysiert, {n} Regeln generiert"

if __name__ == "__main__":
    print(run())
