#!/usr/bin/env python3
import json, sqlite3, os, re
from datetime import datetime
from pathlib import Path
from collections import Counter

JACK_HOME = "/data/data/com.termux/files/home"
PERSONALITY_JSON = f"{JACK_HOME}/jack_personality.json"
PERSONALITY_DB = f"{JACK_HOME}/jack/jack_personality.db"

class PersonalityCollector:
    """Sammelt Daten über Dimitri"""
    
    def __init__(self):
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(PERSONALITY_DB) as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY,
                    ts TEXT,
                    message_text TEXT,
                    tone TEXT,
                    frustration_level INTEGER,
                    energy_level TEXT,
                    decision_speed TEXT,
                    context TEXT
                )
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS patterns (
                    id INTEGER PRIMARY KEY,
                    dimension TEXT,
                    pattern TEXT,
                    frequency INTEGER,
                    last_seen TEXT
                )
            """)
            con.commit()
    
    def analyze_tone(self, text):
        """Erkennt Ton: angry, frustrated, focused, tired, creative, etc."""
        text_lower = text.lower()
        
        if any(w in text_lower for w in ["digga", "einfach", "direkt", "keine zeit"]):
            return "impatient"
        if any(w in text_lower for w in ["verdammt", "scheiss", "nervt"]):
            return "frustrated"
        if any(w in text_lower for w in ["cool", "geil", "perfekt", "hammer"]):
            return "excited"
        if any(w in text_lower for w in ["ich versteh", "müde", "kaputt", "nachtschicht"]):
            return "tired"
        if any(w in text_lower for w in ["warum", "wie", "erklär", "durchdenken"]):
            return "analytical"
        
        return "neutral"
    
    def extract_frustration_triggers(self, text):
        """Findet was dich frustiert"""
        triggers = []
        
        if "warten" in text.lower():
            triggers.append("waiting")
        if "vage" in text.lower() or "nicht klar" in text.lower():
            triggers.append("vague_answers")
        if "hin und her" in text.lower() or "round-and-round" in text.lower():
            triggers.append("circular_discussion")
        if "warum" in text.lower() and "?" in text:
            triggers.append("unclear_reasoning")
        if "nochmal" in text.lower():
            triggers.append("repetition")
        
        return triggers
    
    def estimate_energy(self, text, time_of_day=None):
        """Schätzt dein Energy-Level basierend auf Nachtschicht-Muster"""
        if "nachtschicht" in text.lower() or "kaputt" in text.lower():
            return "low"
        if "produktiv" in text.lower() or "geil" in text.lower():
            return "high"
        if "entspannt" in text.lower() or "joint" in text.lower():
            return "relaxed"
        
        # Basis: Night-Shift = produktiv nachts
        return "unknown"
    
    def analyze_decision_style(self, text):
        """Wie triffst du Entscheidungen?"""
        if "einfach machen" in text.lower() or "probieren" in text.lower():
            return "pragmatic"
        if "durchdenken" in text.lower() or "strategisch" in text.lower():
            return "analytical"
        if "schnell" in text.lower() and "entscheidung" in text.lower():
            return "fast"
        
        return "balanced"
    
    def log_interaction(self, message_text, metadata=None):
        """Speichert eine Interaktion"""
        tone = self.analyze_tone(message_text)
        triggers = self.extract_frustration_triggers(message_text)
        energy = self.estimate_energy(message_text)
        decision = self.analyze_decision_style(message_text)
        frustration = len(triggers)  # 0-5
        
        with sqlite3.connect(PERSONALITY_DB) as con:
            con.execute(
                "INSERT INTO interactions (ts, message_text, tone, frustration_level, energy_level, decision_speed, context) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    datetime.now().isoformat(),
                    message_text[:500],
                    tone,
                    frustration,
                    energy,
                    decision,
                    json.dumps(metadata or {})
                )
            )
            con.commit()
        
        return {
            "tone": tone,
            "frustration_triggers": triggers,
            "energy": energy,
            "decision_style": decision
        }

if __name__ == "__main__":
    pc = PersonalityCollector()
    print("[PERSONALITY] ✓ Collector initialized")

class PersonalityAnalyzer:
    """Wertet gesammelte Daten aus, erkennt echte Patterns"""
    
    def __init__(self):
        self.db = PERSONALITY_DB
    
    def get_tone_distribution(self, limit=100):
        """Welcher Ton dominiert?"""
        with sqlite3.connect(self.db) as con:
            rows = con.execute(
                "SELECT tone, COUNT(*) as count FROM interactions GROUP BY tone ORDER BY count DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return {row[0]: row[1] for row in rows}
    
    def get_frustration_patterns(self):
        """Was frustiert dich am meisten?"""
        with sqlite3.connect(self.db) as con:
            con.row_factory = sqlite3.Row
            rows = con.execute(
                "SELECT * FROM interactions WHERE frustration_level > 0 ORDER BY ts DESC LIMIT 20"
            ).fetchall()
            triggers = {}
            for row in rows:
                try:
                    ctx = json.loads(row['context']) if row['context'] else {}
                except:
                    ctx = {}
                # Parse triggers from message
            return triggers
    
    def get_energy_patterns(self):
        """Dein Energie-Zyklus"""
        with sqlite3.connect(self.db) as con:
            rows = con.execute(
                "SELECT energy_level, COUNT(*) as count FROM interactions WHERE energy_level != 'unknown' GROUP BY energy_level"
            ).fetchall()
            return {row[0]: row[1] for row in rows}
    
    def get_decision_style(self):
        """Wie triffst du Entscheidungen?"""
        with sqlite3.connect(self.db) as con:
            rows = con.execute(
                "SELECT decision_speed, COUNT(*) as count FROM interactions GROUP BY decision_speed"
            ).fetchall()
            return {row[0]: row[1] for row in rows}
    
    def generate_profile(self):
        """Erstellt dein aktuelles Personality-Profil"""
        return {
            "timestamp": datetime.now().isoformat(),
            "tone_distribution": self.get_tone_distribution(),
            "energy_patterns": self.get_energy_patterns(),
            "decision_style": self.get_decision_style(),
            "total_interactions": self._count_interactions(),
        }
    
    def _count_interactions(self):
        with sqlite3.connect(self.db) as con:
            return con.execute("SELECT COUNT(*) FROM interactions").fetchone()[0]

if __name__ == "__main__":
    pa = PersonalityAnalyzer()
    print("[ANALYZER] ✓ Analyzer initialized")

class JackPersonality:
    """Das komplette Personality-System"""
    
    def __init__(self):
        self.collector = PersonalityCollector()
        self.analyzer = PersonalityAnalyzer()
        self.profile = self._load_profile()
    
    def _load_profile(self):
        """Lädt gespeichertes Profil oder erstellt neues"""
        if os.path.exists(PERSONALITY_JSON):
            try:
                with open(PERSONALITY_JSON) as f:
                    return json.load(f)
            except:
                pass
        return self._init_profile()
    
    def _init_profile(self):
        """Initialisiert default Profil"""
        return {
            "owner": "Dimitri",
            "created": datetime.now().isoformat(),
            "tone_dominant": "impatient",
            "frustration_triggers": ["waiting", "vague_answers", "circular_discussion"],
            "energy_cycle": "night_shift_productive",
            "decision_style": "pragmatic_fast",
            "learning_style": "hands_on",
            "context_awareness": {},
            "adaptation_level": 0.5,
        }
    
    def observe(self, message, context=None):
        """JACK beobachtet dich — lernt von jeder Interaktion"""
        analysis = self.collector.log_interaction(message, context)
        self._update_profile(analysis)
        return analysis
    
    def _update_profile(self, new_data):
        """Passt Profil basierend auf neuen Daten an"""
        # Ton aktualisieren
        if "tone" in new_data:
            self.profile["tone_dominant"] = new_data["tone"]
        
        # Triggers tracken
        if "frustration_triggers" in new_data:
            for trigger in new_data["frustration_triggers"]:
                if trigger not in self.profile["frustration_triggers"]:
                    self.profile["frustration_triggers"].append(trigger)
        
        # Energie-Pattern
        if "energy" in new_data:
            self.profile["energy_current"] = new_data["energy"]
        
        self.profile["last_updated"] = datetime.now().isoformat()
        self.save_profile()
    
    def save_profile(self):
        """Speichert Profil in JSON"""
        with open(PERSONALITY_JSON, 'w') as f:
            json.dump(self.profile, f, indent=2)
    
    def get_context_aware_response_style(self):
        """Wie sollte ich mit dir gerade sprechen?"""
        energy = self.profile.get("energy_current", "unknown")
        tone = self.profile.get("tone_dominant", "neutral")
        
        style = {
            "length": "short" if energy == "low" else "medium",
            "formality": "direct" if tone == "impatient" else "conversational",
            "depth": "surface" if energy == "low" else "deep",
            "ask_before": True,  # immer fragen bei Writes
        }
        return style
    
    def predict_frustration(self, action):
        """Würde diese Aktion dich frustieren?"""
        triggers = self.profile.get("frustration_triggers", [])
        
        frustration_map = {
            "waiting": ["timeout", "delay", "slow"],
            "vague_answers": ["unclear", "maybe", "perhaps"],
            "circular_discussion": ["repeat", "again", "same"],
        }
        
        for trigger, keywords in frustration_map.items():
            if trigger in triggers:
                for keyword in keywords:
                    if keyword in str(action).lower():
                        return True, trigger
        
        return False, None

if __name__ == "__main__":
    jp = JackPersonality()
    print("[JACK PERSONALITY] ✓ System ready")
    print(f"[JACK PERSONALITY] Profile loaded: {jp.profile.get('owner')}")
