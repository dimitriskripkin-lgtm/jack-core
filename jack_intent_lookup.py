"""Settings-Navigation mit standardisierten Actions (Qwen 21.08.)
Nutzt Android-Standard-Actions statt interne Activity-Namen."""
import os

# Keyword -> Android Settings Action
SETTINGS_ACTIONS = {
    'wlan': 'android.settings.WIFI_SETTINGS',
    'wifi': 'android.settings.WIFI_SETTINGS',
    'bluetooth': 'android.settings.BLUETOOTH_SETTINGS',
    'display': 'android.settings.DISPLAY_SETTINGS',
    'helligkeit': 'android.settings.DISPLAY_SETTINGS',
    'akku': 'android.settings.BATTERY_SAVER_SETTINGS',
    'battery': 'android.settings.BATTERY_SAVER_SETTINGS',
    'sound': 'android.settings.SOUND_SETTINGS',
    'ton': 'android.settings.SOUND_SETTINGS',
    'notification': 'android.settings.NOTIFICATION_SETTINGS',
    'benachrichtigung': 'android.settings.NOTIFICATION_SETTINGS',
    'apps': 'android.settings.APPLICATION_SETTINGS',
    'anwendungen': 'android.settings.APPLICATION_SETTINGS',
    'storage': 'android.settings.INTERNAL_STORAGE_SETTINGS',
    'speicher': 'android.settings.INTERNAL_STORAGE_SETTINGS',
    'security': 'android.settings.SECURITY_SETTINGS',
    'sicherheit': 'android.settings.SECURITY_SETTINGS',
    'location': 'android.settings.LOCATION_SCANNER_SETTINGS',
    'standort': 'android.settings.LOCATION_SCANNER_SETTINGS',
    'date': 'android.settings.DATE_SETTINGS',
    'datum': 'android.settings.DATE_SETTINGS',
    'zeit': 'android.settings.DATE_SETTINGS',
    'language': 'android.settings.LOCALE_SETTINGS',
    'sprache': 'android.settings.LOCALE_SETTINGS',
    'developer': 'android.settings.APPLICATION_DEVELOPMENT_SETTINGS',
    'entwickler': 'android.settings.APPLICATION_DEVELOPMENT_SETTINGS',
}

def suggest_deep_navigation(user_text):
    """Analysiert User-Text und schlägt Settings-Navigation vor."""
    text_lower = user_text.lower()
    
    # Prüfe ob es eine Settings-Anfrage ist
    if not any(w in text_lower for w in ['einstellungen', 'settings', 'öffne', 'zeige']):
        return None, None
    
    # Suche nach Keyword
    for kw, action in SETTINGS_ACTIONS.items():
        if kw in text_lower:
            intent_cmd = f"am start -a {action}"
            ssh_cmd = f'ssh xiaomi-jack "su -c \'{intent_cmd}\'"'
            return (action,), ssh_cmd
    
    return None, None
