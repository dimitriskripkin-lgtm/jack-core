#!/usr/bin/env python3
import sqlite3, json, subprocess, os, sys, time, shutil
from datetime import datetime

sys.path.append(os.path.expanduser('~/jack'))
import jack_config

DB_PATH = jack_config.get_param('STORAGE', 'db_path')
BACKUP_DIR = os.path.expanduser('~/jack/backups/')
LOG_PATH = os.path.expanduser('~/jack/jack_bug_fixer.log')
HANDSHAKE_PATH = os.path.expanduser('~/jack/jack_handshake.json')
JACK_SUBDIR = os.path.expanduser('~/jack')

HIGH_RISK_PATTERNS = [
    "os.remove", "os.unlink", "shutil.rmtree", "shutil.rmdir",
    "rm -rf", "DROP TABLE", "DELETE FROM", "truncate", "wipe",
    "format(", ".unlink()"
]

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    try:
        with open(LOG_PATH, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass

class JackBugFixer:
    def __init__(self):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        self.db = self._connect_db()
        self.session_fixes = []
        self.session_skipped = []
        self.session_escalated = []

    def _connect_db(self):
        if not os.path.exists(DB_PATH):
            log(f"DB nicht gefunden: {DB_PATH}", "ERROR")
            sys.exit(1)
        return sqlite3.connect(DB_PATH)

    def get_open_errors(self, limit=10):
        try:
            cur = self.db.execute(
                "SELECT id, timestamp, module, error_type, error_msg, "
                "file_path, line_num, context FROM errors "
                "WHERE resolved = 0 ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            return cur.fetchall()
        except sqlite3.OperationalError as e:
            log(f"DB-Schema-Fehler: {e}", "ERROR")
            return []

    def mark_resolved(self, error_id, fix_summary):
        try:
            self.db.execute(
                "UPDATE errors SET resolved = 1, fix_applied = ?, fix_ts = ? WHERE id = ?",
                (fix_summary, datetime.now().isoformat(), error_id)
            )
            self.db.commit()
        except sqlite3.OperationalError as e:
            log(f"Konnte Fehler {error_id} nicht markieren: {e}", "WARN")

    def assess_risk(self, fix_code):
        fix_lower = fix_code.lower()
        for pattern in HIGH_RISK_PATTERNS:
            if pattern.lower() in fix_lower:
                return "HIGH", pattern
        return "LOW", None

    def sandbox_test(self, fix_code, label):
        tmp_dir = os.environ.get("TMPDIR", "/tmp")
        tmp = f"{tmp_dir}/jack_sandbox_{label}_{int(time.time())}.py"
        try:
            with open(tmp, "w") as f:
                f.write(fix_code)
            r = subprocess.run(
                ["python3", "-m", "py_compile", tmp],
                capture_output=True, text=True, timeout=10
            )
            if r.returncode != 0:
                return False, f"SyntaxError: {r.stderr.strip()}"
            return True, "OK"
        except subprocess.TimeoutExpired:
            return False, "Timeout im Sandbox-Test"
        except Exception as e:
            return False, str(e)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def backup_and_apply(self, file_path, fixed_code):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Ziel-Datei nicht gefunden: {file_path}")
        ts = int(time.time())
        backup_name = f"{os.path.basename(file_path)}.bak_{ts}"
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        shutil.copy2(file_path, backup_path)
        log(f"Backup: {backup_path}")
        with open(file_path, "w") as f:
            f.write(fixed_code)
        return backup_path

    def generate_fix(self, module, err_type, err_msg, file_path, line_num, context):
        sys.path.insert(0, JACK_SUBDIR)
        try:
            from jack_code_writer import CodeGenerator
            writer = CodeGenerator()
            original = ""
            if file_path and os.path.exists(file_path):
                with open(file_path, "r") as f:
                    original = f.read()
            prompt = (
                "You are JACK's bug fixer. Fix this Python error precisely.\n\n"
                f"MODULE: {module}\nFILE: {file_path}\nLINE: {line_num}\n"
                f"ERROR TYPE: {err_type}\nERROR MESSAGE: {err_msg}\nCONTEXT: {context}\n\n"
                f"ORIGINAL CODE (komplett):\n{original if original else '(not available)'}\n\n"
                "Rules:\n"
                "- Antworte NUR mit SEARCH/REPLACE-Bloecken in diesem Format:\n"
                "<<<<<<< SEARCH\n(exakter Originaltext)\n=======\n(neuer Text)\n>>>>>>> REPLACE\n"
                "- SEARCH-Text muss BUCHSTABENGENAU im Original vorkommen, inkl. Einrueckung\n"
                "- SEARCH-Text muss EINDEUTIG sein (genug Kontextzeilen)\n"
                "- NIEMALS die ganze Datei zurueckgeben\n"
                "- Kleinstmoegliche Aenderung\n"
                "- Wenn nicht sicher fixbar: antworte exakt CANNOT_FIX\n"
            )
            result = writer.generate(prompt)
            if not result or result.strip() == "CANNOT_FIX":
                return None
            result = result.strip()
            if result.startswith("```"):
                result = "\n".join(result.split("\n")[1:])
            if result.endswith("```"):
                result = "\n".join(result.split("\n")[:-1])
            return result.strip()
        except ImportError:
            log("jack_code_writer nicht importierbar", "ERROR")
            return None
        except Exception as e:
            log(f"generate_fix Fehler: {e}", "ERROR")
            return None

    def escalate_to_dimitri(self, err_id, err_msg, file_path, fix_preview, risk_pattern):
        msg = f"JACK: HIGH-RISK Fix wartet auf OK - {os.path.basename(file_path)}"
        try:
            subprocess.run(["termux-toast", "-s", msg], capture_output=True, timeout=5)
        except Exception as _e:
            import jack_log; jack_log.log_decision('SILENT-FAIL jack_bug_fixer', str(_e)[:120])
        try:
            with open(HANDSHAKE_PATH, "r") as f: hs = json.load(f)
        except Exception: hs = {}
        hs.setdefault("pending_approvals", []).append({
            "error_id": err_id, "file": file_path, "error": err_msg[:200],
            "risk_pattern": risk_pattern, "fix_preview": fix_preview[:300],
            "ts": datetime.now().isoformat(), "status": "waiting"
        })
        try:
            with open(HANDSHAKE_PATH, "w") as f: json.dump(hs, f, indent=2)
            log(f"Eskalation eingetragen (ID: {err_id})")
        except Exception as e:
            log(f"Handshake-Schreiben fehlgeschlagen: {e}", "WARN")

    def update_handshake_summary(self):
        try:
            with open(HANDSHAKE_PATH, "r") as f: hs = json.load(f)
        except Exception: hs = {}
        hs["last_bugfix_session"] = {
            "ts": datetime.now().isoformat(),
            "fixed": len(self.session_fixes),
            "skipped": len(self.session_skipped),
            "escalated": len(self.session_escalated),
            "details": self.session_fixes
        }
        try:
            with open(HANDSHAKE_PATH, "w") as f: json.dump(hs, f, indent=2)
        except Exception as e:
            log(f"Handshake-Update fehlgeschlagen: {e}", "WARN")

    def run(self):
        log("=== JACK BugFixer gestartet ===")
        errors = self.get_open_errors()
        if not errors:
            log("Keine offenen Fehler. System sauber.")
            return
        log(f"{len(errors)} Fehler gefunden. Starte Analyse...")
        for row in errors:
            err_id, ts, module, err_type, err_msg, file_path, line_num, context = row
            label = f"{module}#{err_id}"
            log(f"--- [{label}] {err_type} in {module} ---")
            log(f"Datei: {file_path}:{line_num}")
            fix_code = self.generate_fix(module, err_type, err_msg, file_path, line_num, context)
            if not fix_code:
                log("[SKIP] Kein Fix generierbar.", "WARN")
                self.session_skipped.append(label)
                continue
            risk, pattern = self.assess_risk(fix_code)
            if risk == "HIGH":
                log(f"[HIGH-RISK] Pattern '{pattern}' - Dimitri muss bestaetigen!", "WARN")
                self.escalate_to_dimitri(err_id, err_msg, file_path, fix_code, pattern)
                self.session_escalated.append(label)
                continue
            try:
                import jack_patch
                ok2, msg2, preview = jack_patch.safe_patch(file_path, fix_code)
                if not ok2:
                    log(f"[PATCH ABGELEHNT] {msg2}", "WARN")
                    self.session_skipped.append(label)
                    continue
                log(f"[DIFF]\n{preview}")
                self.mark_resolved(err_id, f"AutoFixed {err_type} @ line {line_num}")
                self.session_fixes.append(f"{label}: fixed {err_type}")
                log(f"[FIXED] {msg2}")
            except Exception as e:
                log(f"[APPLY FAIL] {e}", "ERROR")
                self.session_skipped.append(label)
        log("=== Session Abgeschlossen ===")
        log(f"Fixes: {len(self.session_fixes)}  Eskaliert: {len(self.session_escalated)}  Uebersprungen: {len(self.session_skipped)}")
        self.update_handshake_summary()
        self.db.close()

if __name__ == "__main__":
    JackBugFixer().run()
