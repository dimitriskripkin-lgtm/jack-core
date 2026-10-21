#!/usr/bin/env python3
"""JACK_TUNE_FAHRDIGEST20C – Abbruchschutz und einmaliges Fahrtdigest (OFFLINE ENTWURF).

Nur mit JACK_TUNE_TG_BUFFER_OFF -> PUFFER_AKTIV=True UND einem kontrollierten
60-Sekunden-Tick aktivieren. Kein eigener Daemon. Bluetooth ist nur ein Kontextsignal.
Task-Resultat 'GESENDET' bedeutet Telegram-ACK, nicht vom Menschen gelesen.
Die Queue-Zustellung ist at-least-once; Absturz NACH Telegram-ACK und VOR ACK-Datei
kann dieselbe Sammelmeldung wiederholen. Digest-ID erleichtert Duplikat-Erkennung.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time

import jack_tg_send as tg

STATE = tg.HOME / 'logs' / 'telegram_fahrt_state.json'
DIGEST_LOCK = tg.HOME / 'logs' / '.fahrt_digest.lock'
OFF_SECONDS = 120
MAX_SENSOR_AGE = 120
MAX_STATE_AGE = 600
MAX_QUEUE_ROWS = 1500
MAX_DIGEST = 3400


def _state():
    try:
        st = json.loads(STATE.read_text(encoding='utf-8'))
        return st if isinstance(st, dict) else {}
    except (OSError, ValueError):
        return {}


def _atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.fahrt-', suffix='.tmp', dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as fp:
            fp.write(data)
            fp.flush()
            os.fsync(fp.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _save(st):
    _atomic(STATE, json.dumps(st, ensure_ascii=False, separators=(',', ':')) + '\n')


def should_buffer(now=None):
    """Waehrend aktiver Fahrt UND der 2-Minuten-Trennungsfrist puffern.

    Kein unendlicher Ausfall-Puffer: wenn Watcher seit >10 Min kein Ergebnis hat,
    duerfen nichtkritische Nachrichten wieder regulär gesendet werden.
    """
    now = time.time() if now is None else now
    if tg._fahre(zeit=now):
        return True
    st = _state()
    age = now - st.get('aktualisiert', -1e12)
    return st.get('modus') in ('FAHRT', 'TRENNUNG') and 0 <= age <= MAX_STATE_AGE


def _sensor():
    import jack_lagebild
    return jack_lagebild.fahrmodus()  # bestehende Messung, aktualisiert .fahrmodus


def _fresh(sample, now):
    if not isinstance(sample, dict) or sample.get('unsicher') is True:
        return None
    t = sample.get('geprueft')
    if type(t) not in (int, float) or not -5 <= now - t <= MAX_SENSOR_AGE:  # CLAUDE: Messung kann nach now liegen (Kap 299)
        return None
    return sample.get('aktiv') if type(sample.get('aktiv')) is bool else None


def _read_queue():
    """Queue-Snapshot unter DEMSELBEN Lock wie jede append-Operation."""
    tg.LOCK.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(tg.LOCK, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        if not tg.QUEUE.exists():
            return []
        if tg.QUEUE.stat().st_size > tg.MAX_QUEUE:
            raise ValueError('QUEUE_ZU_GROSS')
        result = []
        for line in tg.QUEUE.read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            if not isinstance(item, dict) or not re.fullmatch(r'[0-9a-f]{32}', str(item.get('id',''))):
                raise ValueError('QUEUE_UNGUELTIG')
            if item.get('route') not in ('default', 'vinted') or item.get('status') != 'GEPUFFERT':
                raise ValueError('QUEUE_UNGUELTIG')
            result.append(item)
            if len(result) > MAX_QUEUE_ROWS:
                raise ValueError('QUEUE_ZU_VIELE')
        return result
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _ack(ids):
    """Nur Snapshot-IDs entfernen, neue parallele Eintraege erhalten."""
    fd = os.open(tg.LOCK, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        if not tg.QUEUE.exists():
            return
        remaining = []
        for line in tg.QUEUE.read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            if item.get('id') not in ids:
                remaining.append(line)
        _atomic(tg.QUEUE, ('\n'.join(remaining) + '\n') if remaining else '')
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _digest(items):
    ids = sorted({i['id'] for i in items})
    digest_id = hashlib.sha256(('|'.join(ids)).encode()).hexdigest()[:12]
    counts = {}
    for i in items:
        q = str(i.get('quelle') or 'unbekannt')[:36]
        counts[q] = counts.get(q, 0) + 1
    rows = [f'JACK: Sammelmeldung nach Fahrt ({len(items)} Hinweise).',
            f'Kennung: {digest_id} (bei doppelter Meldung ignorieren).',
            'Zusammenfassung nach Quelle:']
    rows.extend(f'- {key}: {counts[key]}' for key in sorted(counts))
    rows.append('Auszug (nur Hauptbot, Vinted nur als Anzahl):')
    shown = 0
    for i in items:
        if i.get('route') != 'default':
            continue
        if shown >= 8:
            break
        msg = ' '.join(str(i.get('text') or '').split())
        msg = re.sub(r'(?i)Bearer\s+\S+|gh[pousr]_[A-Za-z0-9_]{12,}|sk-[A-Za-z0-9_-]{15,}', '[GESCHUETZT]', msg)
        msg = msg[:120]
        entry = f'- {str(i.get("quelle") or "system")[:36]}: {msg}'
        if len('\n'.join(rows+[entry])) > MAX_DIGEST - 100:
            break
        rows.append(entry)
        shown += 1
    if len(items) > shown:
        rows.append('Weitere Hinweise nur als Anzahl erfasst (keine Rohtexte an KI).')
    return '\n'.join(rows)[:MAX_DIGEST], digest_id


def tick(now=None, sample=None, send_func=None):
    """Ein kontrollierter Aufruf (z.B. cron * * * * *), keine Endlosschleife.

    sample / send_func sind Offline-Test-Injektionen, niemals aus freien MCP-Acts.
    """
    if tg.PUFFER_AKTIV is not True:
        return {'status': 'AUS', 'grund': 'PUFFER_AKTIV_FALSE'}
    now = time.time() if now is None else now
    DIGEST_LOCK.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(DIGEST_LOCK, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {'status': 'BESCHAEFTIGT'}
        try:
            try:
                sample = _sensor() if sample is None else sample
            except Exception as e:
                return {'status': 'UNSICHER', 'grund': 'SENSOR_' + type(e).__name__}
            active = _fresh(sample, now)
            st = _state()
            mode = st.get('modus', 'IDLE')
            if active is None:
                return {'status': 'UNSICHER', 'grund': 'KEINE_FRISCHE_BT_MESSUNG'}
            if active:
                _save({'modus': 'FAHRT', 'aktualisiert': now, 'getrennt_seit': None})
                return {'status': 'FAHRT'}
            if mode != 'TRENNUNG':
                try:
                    backlog = _read_queue()
                except (OSError, ValueError):
                    return {'status': 'FEHLER', 'grund': 'QUEUE_UNLESBAR'}
                if mode == 'IDLE' and not backlog:
                    _save({'modus': 'IDLE', 'aktualisiert': now})
                    return {'status': 'IDLE'}
                _save({'modus': 'TRENNUNG', 'aktualisiert': now, 'getrennt_seit': now})
                return {'status': 'WARTET', 'sekunden': OFF_SECONDS}
            since = st.get('getrennt_seit')
            if type(since) not in (int, float) or now < since:
                _save({'modus': 'TRENNUNG', 'aktualisiert': now, 'getrennt_seit': now})
                return {'status': 'WARTET', 'sekunden': OFF_SECONDS}
            if now - since < OFF_SECONDS:
                _save({'modus': 'TRENNUNG', 'aktualisiert': now, 'getrennt_seit': since})
                return {'status': 'WARTET', 'sekunden': int(OFF_SECONDS-(now-since))}
            try:
                items = _read_queue()
            except (OSError, ValueError):
                return {'status': 'FEHLER', 'grund': 'QUEUE_UNLESBAR'}
            if not items:
                _save({'modus': 'IDLE', 'aktualisiert': now})
                return {'status': 'LEER'}
            body, digest_id = _digest(items)
            deliver = send_func or tg.send
            result = deliver(body, wichtig=True, quelle='fahrdigest')
            if not isinstance(result, dict) or result.get('status') != 'GESENDET':
                return {'status': 'SENDEN_FEHLER', 'grund': 'KEIN_TELEGRAM_ACK', 'id': digest_id}
            try:
                _ack({i['id'] for i in items})
                rest = _read_queue()
            except (OSError, ValueError):
                return {'status': 'ACK_FEHLER', 'id': digest_id,
                        'hinweis': 'Telegram hat bestaetigt, Queue-ACK unklar; Duplikat moeglich'}
            _save({'modus': 'IDLE' if not rest else 'TRENNUNG', 'aktualisiert': now,
                   'getrennt_seit': now if rest else None, 'letztes_digest': digest_id})
            return {'status': 'GESENDET', 'anzahl': len(items), 'id': digest_id, 'rest': len(rest)}
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


if __name__ == '__main__':
    print(json.dumps(tick(), ensure_ascii=False))
