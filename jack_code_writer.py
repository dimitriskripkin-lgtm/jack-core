#!/usr/bin/env python3
import os, json, subprocess, re
from datetime import datetime
from pathlib import Path

JACK_HOME = "/data/data/com.termux/files/home"
SAFE_DIRS = [JACK_HOME, "/data/local/tmp"]
FORBIDDEN_DIRS = ["/system/", "/data/system/", "/data/app/", "/data/data/"]
MEMORY_DB = f"{JACK_HOME}/jack/jack_memory.db"

class CodeWriter:
    def __init__(self):
        self.workspace = JACK_HOME
    
    def is_safe_path(self, filepath):
        """Checkt ob Pfad sicher ist"""
        p = str(Path(filepath).resolve())
        
        # Safe-Check ZUERST - spezifischere Allow-List gewinnt
        for safe in SAFE_DIRS:
            if p.startswith(safe):
                return True, None
        
        # Forbidden paths
        for forbidden in FORBIDDEN_DIRS:
            if p.startswith(forbidden):
                return False, f"Forbidden: {forbidden}"
        
        return False, "Outside sandbox"
    
    def needs_approval(self, filepath, operation):
        """Checkt ob Benutzer fragen muss"""
        safe, reason = self.is_safe_path(filepath)
        
        if not safe:
            return True, f"UNSAFE: {reason}"
        
        # Edit bestehender Dateien = fragen
        if operation == "edit" and os.path.exists(filepath):
            return True, "Editing existing file"
        
        # Neue scripts in jack_home = ok
        if operation == "create" and str(filepath).endswith(".py"):
            return False, "New script"
        
        return False, None
    
    def write_code(self, filepath, code, operation="create"):
        """Schreibt Code mit Approval-Check"""
        safe, reason = self.is_safe_path(filepath)
        
        if not safe:
            return {"success": False, "error": f"BLOCKED: {reason}"}
        
        needs_ask, reason = self.needs_approval(filepath, operation)
        
        if needs_ask:
            print(f"\n[WRITER] Approval needed:")
            print(f"  File: {filepath}")
            print(f"  Op: {operation.upper()}")
            print(f"  Reason: {reason}")
            response = input("  Proceed? (ja/nein): ").strip().lower()
            if response not in ["ja", "j", "yes", "y"]:
                return {"success": False, "error": "User denied"}
        
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                f.write(code)
            return {"success": True, "filepath": filepath, "bytes": len(code)}
        except Exception as e:
            return {"success": False, "error": str(e)}

if __name__ == "__main__":
    cw = CodeWriter()
    print("[WRITER] ✓ CodeWriter initialized")

from google import genai
from google.genai import types

class CodeGenerator:
    def __init__(self):
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("[GEN] GEMINI_API_KEY nicht gesetzt!")
        self.client = genai.Client(api_key=key)
        self.model = "gemini-2.5-flash"
    
    def generate(self, prompt, language="python"):
        """Generiert Code via Gemini"""
        sys_prompt = f"""Du bist ein Expert-Programmierer. Generiere nur Code, nichts anderes.
        - Language: {language}
        - Format: nur Code, kein Erklärtext
        - Qualität: Production-ready, mit Error-Handling
        - Style: Kurz, effizient, keine Redundanz
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    
                    types.Part.from_text(f"Generiere: {prompt}")
                ]
            )
            return response.text.strip()
        except Exception as e:
            return f"[ERROR] {e}"

if __name__ == "__main__":
    try:
        gen = CodeGenerator()
        print(f"[GEN] ✓ CodeGenerator ready ({gen.model})")
    except RuntimeError as e:
        print(f"[GEN] {e}")

class JackCodeWriter:
    def __init__(self):
        self.writer = CodeWriter()
        self.gen = CodeGenerator()
    
    def write(self, prompt, filepath, language="python"):
        """Generiert Code UND schreibt ihn"""
        print(f"[JACK CODE] Generating: {prompt}")
        code = self.gen.generate(prompt, language)
        
        if "[ERROR]" in code:
            return {"success": False, "error": code}
        
        print(f"\n[JACK CODE] Preview ({len(code)} chars):")
        lines = code.split('\n')[:10]
        for line in lines:
            print(f"  {line}")
        if len(code.split('\n')) > 10:
            print(f"  ... ({len(code.split('\n'))-10} more lines)")
        
        result = self.writer.write_code(filepath, code)
        
        if result["success"]:
            print(f"\n✓ Written: {filepath}")
        
        return result

if __name__ == "__main__":
    jack = JackCodeWriter()
    print("[JACK CODE] ✓ System ready")
