import re

MUSTER = [
    (r'rm\s+-rf\s+[~/]', 'rm -rf auf Systempfad'),
    (r'/tmp/', 'nutzt /tmp statt ~/jack'),
    (r'\bping\b', 'nutzt ping - kein ICMP auf Android'),
    (r'chromadb', 'ChromaDB verboten'),
    (r'while\s+True:\s*$', 'Endlosschleife ohne sleep'),
    (r'(api[_-]?key|token)\s*=\s*["\']\w{15,}', 'Klartext-Geheimnis'),
    (r'os\.system\(', 'os.system statt subprocess'),
    (r'pip\s+install\s+--upgrade\s+cryptography', 'cryptography-Upgrade verboten'),
]

def pruefe(inhalt):
    treffer = []
    for muster, grund in MUSTER:
        if re.search(muster, inhalt, re.I | re.M):
            treffer.append(grund)
    if not treffer:
        return True, 'sauber'
    return False, ' | '.join(treffer)
