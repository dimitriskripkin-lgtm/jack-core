"""Schöne Konsolen-Ausgabe mit ANSI-Farben und Box-Drawing"""

class C:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

B = {
    'H': '─', 'V': '│', 'TL': '┌', 'TR': '┐',
    'BL': '└', 'BR': '┘', 'L': '├', 'R': '┤'
}

def header(title, width=48):
    top = B['TL'] + B['H'] * (width - 2) + B['TR']
    bot = B['BL'] + B['H'] * (width - 2) + B['BR']
    empty = B['V'] + ' ' * (width - 2) + B['V']
    center = f" {title} ".center(width - 2)
    text = B['V'] + center + B['V']
    print(f"{C.CYAN}{C.BOLD}{top}{C.RESET}")
    print(f"{C.CYAN}{empty}{C.RESET}")
    print(f"{C.CYAN}{text}{C.RESET}")
    print(f"{C.CYAN}{empty}{C.RESET}")
    print(f"{C.CYAN}{bot}{C.RESET}")

def box(lines, width=48, title=None):
    top = B['TL'] + B['H'] * (width - 2) + B['TR']
    print(f"{C.CYAN}{top}{C.RESET}")
    if title:
        t = B['V'] + f" {title} ".center(width - 2) + B['V']
        print(f"{C.CYAN}{t}{C.RESET}")
        print(f"{C.CYAN}{B['L'] + B['H'] * (width - 2) + B['R']}{C.RESET}")
    for line in lines:
        if len(line) > width - 4:
            line = line[:width-4]
        padded = f" {line} ".ljust(width - 2)
        print(f"{C.CYAN}{B['V']}{C.RESET}{padded}{C.CYAN}{B['V']}{C.RESET}")
    print(f"{C.CYAN}{B['BL'] + B['H'] * (width - 2) + B['BR']}{C.RESET}")

def status(label, value, color=C.WHITE):
    print(f"{C.DIM}•{C.RESET} {C.BOLD}{label}:{C.RESET} {color}{value}{C.RESET}")

def ok(msg): print(f"{C.GREEN}✓ {msg}{C.RESET}")
def fail(msg): print(f"{C.RED}✗ {msg}{C.RESET}")
def warn(msg): print(f"{C.YELLOW}⚠ {msg}{C.RESET}")
def info(msg): print(f"{C.CYAN}ℹ {msg}{C.RESET}")

def progress(current, total, width=30, label=""):
    pct = current / total if total > 0 else 0
    filled = int(width * pct)
    bar = (C.GREEN + '█' * filled + C.DIM + '░' * (width - filled) + C.RESET)
    txt = f"{pct*100:5.1f}%"
    if label:
        print(f"{C.BOLD}{label}{C.RESET} {bar} {txt}")
    else:
        print(f"{bar} {txt}")

if __name__ == '__main__':
    header("JACK UI TEST")
    box([
        "Diese UI-Bibliothek macht die",
        "Konsolen-Ausgabe schicker.",
        "",
        "Verfügbar in ganz JACK!"
    ], title="Info")
    print()
    status("Version", "1.0", C.CYAN)
    status("Status", "OK", C.GREEN)
    print()
    ok("Das funktioniert")
    warn("Eine Warnung")
    fail("Ein Fehler")
    print()
    progress(7, 10, label="Fortschritt")
