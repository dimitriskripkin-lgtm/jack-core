"""JACK Recovery v1 (Kap 288): deterministischer Klassifikator, Budget 2, nie SUCCESS.
Kein SSH, kein Bild. Der Aufrufer (jack_ui_agent Kern) fuehrt aus und beobachtet frisch.
JACK_TUNE_RECOVERY_V1. Basis ChatGPT Review 3 (sha a8dfe391), Claude: Bounds wie jack_ghost._mitte.
"""
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

SAFE_DISMISS = {'schließen', 'schliessen', 'später', 'spaeter', 'nicht jetzt', 'abbrechen', 'cancel', 'close', 'later'}
AUTH = re.compile(r'passwort|password|anmelden|sign.?in|log.?in|2fa|two.factor|authenticat|konto auswählen|pin eingeben|otp|verification code', re.I)
PERMISSION = re.compile(r'permission|berechtigung|zulassen|erlauben|allow access|while using|nur dieses mal|nur dieses mal|standortzugriff', re.I)
NETWORK = re.compile(r'err_[a-z_]+|keine internetverbindung|no internet|network error|netzwerkfehler|webseite nicht verfügbar', re.I)
DIALOG_CLASS = re.compile(r'dialog|alertdialog', re.I)
FORBIDDEN = re.compile(r'wlan|wi-?fi|flugmodus|flugzeug|mobile daten|hotspot|debugging|entwickler|ausschalten|neu starten|zur.cksetzen|werkseinstell|l.sch(en|ung)|deinstall|kauf|bezahl|zahlung|abonn|senden|teilen|reset|factory.reset', re.I)
SYSTEM_PACKAGES = {'com.android.permissioncontroller', 'com.google.android.permissioncontroller', 'com.android.systemui'}

@dataclass
class Context:
    target_app: str = ''
    allowed_apps: set = field(default_factory=set)
    foreground: str = ''
    xml: str = ''
    keyguard: bool = False
    transport_ok: bool = True
    signatures: tuple = ()
    navigation_expected: bool = False
    known_parent: bool = False
    wrong_state: bool = False
    screen_off: bool = False

@dataclass
class Result:
    cls: str = 'UNKNOWN'
    action: str = 'abort'
    reason: str = 'unbekannter Zustand'
    button: int = 0
    evidence: str = ''

class Budget:
    def __init__(self):
        self.count = 0
        self.last_class = None

    def permit(self, cls):
        if self.count >= 2 or self.last_class == cls:
            return False
        self.count += 1
        self.last_class = cls
        return True


def classify(ctx):
    """Classify without reading another UI or issuing commands. Fail closed."""
    if not ctx.transport_ok:
        return Result('R09', 'abort', 'WORKER_OFFLINE', evidence='transport unreachable')
    if ctx.keyguard:
        return Result('R10', 'abort', 'LOCKED_ABORT', evidence='keyguard=true')
    if ctx.screen_off:
        return Result('R10', 'wake', 'SCREEN_OFF', evidence='display off, keyguard=false')
    if ctx.foreground and ctx.foreground not in ctx.allowed_apps:
        if ctx.foreground in SYSTEM_PACKAGES:
            return Result('R02', 'abort', 'SYSTEM_DIALOG_UNBEWIESEN', evidence='system foreground')
        return Result('R08', 'abort', 'FOREIGN_APP', evidence='foreground not allowlisted')
    if not ctx.foreground:
        return Result('UNKNOWN', 'abort', 'FOREGROUND_UNKNOWN')
    try:
        root = ET.fromstring(ctx.xml)
    except (ET.ParseError, TypeError):
        return Result('R07', 'wait', 'BAD_XML', evidence='XML invalid or absent')
    nodes = list(root.iter('node'))
    if not nodes:
        return Result('R07', 'wait', 'EMPTY_XML', evidence='no nodes')
    labels = []
    buttons = []
    node_labels = []
    clickable_nodes = []
    permission_buttons = []
    password_field = False
    dialog = False
    for n in nodes:
        label = (n.get('text') or n.get('content-desc') or '').strip()
        if label:
            labels.append(label)
            node_labels.append((label, n.get('class') or ''))
        if n.get('password', '').lower() == 'true':
            password_field = True
        if DIALOG_CLASS.search(n.get('class') or ''):
            dialog = True
        if n.get('clickable') == 'true':
            clickable_nodes.append(n)
            # Exactly _lese_ui: clickable nodes with bounds parsed like jack_ghost._mitte and y < 2100.
            m = re.findall(r'-?[0-9]+', n.get('bounds', '') or '')
            if len(m) != 4 or (int(m[1])+int(m[3]))//2 >= 2100:
                continue
            if not label:
                children = [(k.get('text') or k.get('content-desc') or '').strip() for k in n.iter('node') if k is not n]
                label = ' / '.join(t for t in children if t)[:40]
            buttons.append((len(buttons)+1, label))
            if re.fullmatch(r'(?i)(zulassen|erlauben|allow|allow only while using|nur dieses mal)', label):
                permission_buttons.append(label)
    combined = ' '.join(labels)[:16000]
    # JACK_TUNE_RECOVERY_FP: page-wide prose is never sufficient evidence.
    if password_field or (dialog and AUTH.search(combined)):
        return Result('R03', 'abort', 'LOGIN_REQUIRED', evidence='password field or auth dialog')
    permission_package = ctx.foreground in {'com.android.permissioncontroller', 'com.google.android.permissioncontroller'}
    if permission_package or (dialog and permission_buttons):
        return Result('R02', 'abort', 'PERMISSION_UNBEWIESEN', evidence='permission controller or permission dialog')
    # Error page, not a snippet containing "ERR_": dedicated error node and sparse UI.
    error_nodes = [t for t, _ in node_labels if NETWORK.fullmatch(t.strip()) or
                   (NETWORK.search(t) and len(t) <= 85 and not re.search(r'(?i)(beispiel|example|code|suche|suchergebnis)', t))]
    if error_nodes and len(labels) <= 8 and not dialog:
        return Result('R06', 'wait', 'NETWORK_RETRY_ONCE', evidence='sparse error screen')
    if dialog:
        # A negative button does NOT make a dangerous confirmation safe to handle.
        if FORBIDDEN.search(combined):
            return Result('R01', 'abort', 'FORBIDDEN_DIALOG', evidence='dangerous dialog context')
        matches = [(i, t) for i, t in buttons if t.casefold().strip() in SAFE_DISMISS and not FORBIDDEN.search(t)]
        if len(matches) == 1:
            return Result('R01', 'dismiss', 'SAFE_POPUP', matches[0][0], 'one unambiguous dismiss label')
        return Result('UNKNOWN', 'abort', 'AMBIGUOUS_DIALOG', evidence='dialog with no unique safe dismiss')
    if len(ctx.signatures) >= 4 and len(set(ctx.signatures[-4:])) == 1:
        return Result('R05', 'back', 'STUCK', evidence='4 identical signatures')
    if ctx.wrong_state and ctx.navigation_expected and ctx.known_parent:
        return Result('R04', 'back', 'WRONG_STATE', evidence='known safe parent')
    if not labels and not buttons:
        return Result('R07', 'wait', 'NO_VISIBLE_NODES', evidence='no text/clickable nodes')
    return Result('UNKNOWN', 'none', 'NO_RECOVERY_INDICATED')


def decide(ctx, budget):
    r = classify(ctx)
    if r.action in ('abort', 'none'):
        return r
    if not budget.permit(r.cls):
        return Result(r.cls, 'abort', 'RECOVERY_BUDGET_OR_REPEAT', evidence=r.evidence)
    return r
