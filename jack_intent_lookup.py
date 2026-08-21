"""Intent-Katalog: Deep-Navigation für Settings (Qwen 21.08.)
Nutzt 19415 Intents aus jack_cmd_crawler.db für präzise Navigation."""
import sqlite3, os, re

J = os.path.expanduser("~/jack")
DB_PATH = os.path.join(J, "jack_cmd_crawler.db")

# Keyword -> Package + Component-Teil
SETTINGS_MAP = {
    'wlan': ('com.android.settings', 'ConfigureWifi'),
    'wifi': ('com.android.settings', 'ConfigureWifi'),
    'bluetooth': ('com.android.settings', 'Bluetooth'),
    'display': ('com.android.settings', 'Display'),
    'helligkeit': ('com.android.settings', 'Display'),
    'akku': ('com.android.settings', 'Battery'),
    'battery': ('com.android.settings', 'Battery'),
    'sound': ('com.android.settings', 'Sound'),
    'ton': ('com.android.settings', 'Sound'),
    'notification': ('com.android.settings', 'Notification'),
    'benachrichtigung': ('com.android.settings', 'Notification'),
    'apps': ('com.android.settings', 'Application'),
    'anwendungen': ('com.android.settings', 'Application'),
    'storage': ('com.android.settings', 'Storage'),
    'speicher': ('com.android.settings', 'Storage'),
    'security': ('com.android.settings', 'Security'),
    'sicherheit': ('com.android.settings', 'Security'),
    'location': ('com.android.settings', 'Location'),
    'standort': ('com.android.settings', 'Location'),
    'date': ('com.android.settings', 'DateTime'),
    'datum': ('com.android.settings', 'DateTime'),
    'zeit': ('com.android.settings', 'DateTime'),
    'language': ('com.android.settings', 'LocalePicker'),
    'sprache': ('com.android.settings', 'LocalePicker'),
    'developer': ('com.android.settings', 'DevelopmentSettings'),
    'entwickler': ('com.android.settings', 'DevelopmentSettings'),
}

def find_settings_intent(keyword):
    """Sucht Settings-Intent basierend auf Keyword."""
    kw = keyword.lower()
    if kw not in SETTINGS_MAP:
        return None
    
    package, component_part = SETTINGS_MAP[kw]
    
    try:
        con = sqlite3.connect(DB_PATH, timeout=5)
        query = """
            SELECT package, component, action
            FROM intents
            WHERE package = ? AND component LIKE ?
            LIMIT 1
        """
        row = con.execute(query, (package, f'%{component_part}%')).fetchone()
        con.close()
        return row
    except Exception:
        return None

def build_deep_command(intent_row):
    """Baut SSH-Befehl für Deep-Navigation."""
    if not intent_row:
        return None
    
    package, component, action = intent_row
    
    # Component ist oft .ActivityName, muss zu package/.ActivityName werden
    if component.startswith('.'):
        full_component = package + component
    else:
        full_component = component
    
    # Intent-Parameter bauen
    intent_parts = ['am', 'start', '-n', full_component]
    
    if action and action != 'android.intent.action.VIEW':
        intent_parts.extend(['-a', action])
    
    intent_cmd = ' '.join(intent_parts)
    ssh_cmd = f'ssh xiaomi-jack "su -c \'{intent_cmd}\'"'
    
    return ssh_cmd

def suggest_deep_navigation(user_text):
    """Analysiert User-Text und schlägt Deep-Navigation vor."""
    text_lower = user_text.lower()
    
    # Prüfe ob es eine Settings-Anfrage ist
    if not any(w in text_lower for w in ['einstellungen', 'settings', 'öffne', 'zeige']):
        return None, None
    
    # Suche nach Keyword
    for kw in SETTINGS_MAP:
        if kw in text_lower:
            intent = find_settings_intent(kw)
            if intent:
                return intent, build_deep_command(intent)
    
    return None, None
