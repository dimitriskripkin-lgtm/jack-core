#!/usr/bin/env python3
"""JACK_TUNE_TGSEND20B: Telegram-Benachrichtigungen zentral senden oder im Fahrmodus puffern.

Nur Entwurf: nicht auf HONOR installieren ohne Claude-Review/Dima-Go.
20c (Flush/Digest beim Aussteigen) wird als getrenntes Modul eingebunden.
Kap.293: logs/telegram_chat.jsonl: {ts, von, text[:2000]}; 2MB .1 Rotation.
"""
import fcntl
import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.request
import uuid

HOME = Path(os.environ.get('JACK_HOME', '/data/data/com.termux/files/home/jack'))
LOG = HOME / 'logs' / 'telegram_chat.jsonl'
QUEUE = HOME / 'logs' / 'telegram_fahrt_queue.jsonl'
LOCK = HOME / 'logs' / '.tg_send.lock'
FAHR = HOME / '.fahrmodus'
SECRETS = Path(os.path.expanduser('~/.jack_secrets'))
MAX_LOG = 2_000_000
MAX_QUEUE = 1_000_000
MAX_TEXT = 12000
CHUNK = 3500
PUFFER_AKTIV = True  # JACK_TUNE_TG_BUFFER_OFF: explizite Aktivierung nur mit 20c + Dima-Go


def _audit(event, quelle, grund=''):
    # Niemals Text, URL, Telegram-Token oder Chat-ID in Fehlermeldungen schreiben.
    try:
        import jack_log
        jack_log.log_decision('TGSEND-' + event, str(quelle)[:36] + ':' + str(grund)[:70])
    except Exception:
        import sys
        print('TGSEND-' + event + ' ' + str(quelle)[:36] + ' ' + str(grund)[:70], file=sys.stderr)


def _now():
    return time.strftime('%Y-%m-%d %H:%M:%S')


def _conf():
    values = {}
    with open(SECRETS, encoding='utf-8') as f:
        for row in f:
            if '=' in row:
                k, v = row.split('=', 1)
                k = k.strip()
                if k.startswith('export '):
                    k = k[7:].strip()  # echtes Format: export TELEGRAM_BOT_TOKEN="..."
                if k in ('TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID'):
                    values[k] = v.strip().strip('\"\'')
    return values.get('TELEGRAM_BOT_TOKEN'), values.get('TELEGRAM_CHAT_ID')


def _fahre(zeit=None):
    """Nur frisch und sicher belegter LKW-Bluetooth-Zustand; kein Poller/kein Systemaufruf."""
    zeit = time.time() if zeit is None else zeit
    try:
        st = json.loads(FAHR.read_text(encoding='utf-8'))
        return (st.get('aktiv') is True and st.get('unsicher') is not True
                and type(st.get('geprueft')) in (float, int)
                and 0 <= zeit - st['geprueft'] <= 120)
    except (OSError, ValueError, TypeError, KeyError):
        return False


def _buffer_during_drive():
    """20c-State kontrolliert Bluetooth-Abbrueche; bei fehlendem Modul nur
    frisch bestaetigte aktive Fahrt puffern (kein Crash/kein Blockieren).
    """
    try:
        import jack_fahrt_digest
        return jack_fahrt_digest.should_buffer()
    except ImportError:
        return _fahre()
    except Exception:
        _audit('FAHRTSTATUSFEHLER', 'system', 'state_invalid')
        return _fahre()


def _record(path, item, max_size=None, rotate=False):
    """Ein einzelner O_APPEND-write mit flock fuer konkurrierende HELFER-Prozesse."""
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(item, ensure_ascii=False, separators=(',', ':')) + '\n').encode()
    fdlock = os.open(LOCK, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fdlock, fcntl.LOCK_EX)
        current = path.stat().st_size if path.exists() else 0
        if max_size and current + len(encoded) > max_size:
            if not rotate:
                raise OSError('QUEUE_VOLL')
            # Wie Kap.293: nur eine Generation, NICHT garantiert atomar mit jack_telegram._chatlog.
            os.replace(path, Path(str(path) + '.1'))
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            os.write(fd, encoded)
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        fcntl.flock(fdlock, fcntl.LOCK_UN)
        os.close(fdlock)


def _deliver(payload, tok, cid, timeout=10):
    data = json.dumps({'chat_id': cid, 'text': payload}, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request('https://api.telegram.org/bot' + tok + '/sendMessage',
                                 data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        result = json.loads(resp.read(65536).decode('utf-8'))
    if result.get('ok') is not True:
        raise ValueError('TELEGRAM_NOT_OK')


def send(text, wichtig=True, quelle='system', *, bot_token=None, chat_id=None, route='default'):
    """Rueckgabe dict: status GESENDET|GEPUFFERT|FEHLER, keine erfundenen Zustellungen.

    PUFFER_AKTIV=False: auch unwichtige Meldungen werden normal gesendet.
    PUFFER_AKTIV=True: Fahrmodus-/Abbruchschutz nach 20c, lokale Queue.
    Für Vinted separate Bot-/Chat-Credentials explizit übergeben; nie im Log/Queue speichern.
    """
    quelle = str(quelle or 'system')[:36]
    if not re.fullmatch(r'[a-zA-Z0-9_:-]{1,36}', quelle):
        return {'status': 'FEHLER', 'grund': 'QUELLE_UNGUELTIG'}
    if route not in ('default', 'vinted'):
        return {'status': 'FEHLER', 'grund': 'ROUTE_UNGUELTIG'}
    if not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT:
        return {'status': 'FEHLER', 'grund': 'TEXT_UNGUELTIG'}
    if type(wichtig) is not bool:
        return {'status': 'FEHLER', 'grund': 'WICHTIG_UNGUELTIG'}
    if (bot_token is None) != (chat_id is None):
        return {'status': 'FEHLER', 'grund': 'EMPFAENGER_UNVOLLSTAENDIG'}
    if bot_token is not None and route != 'vinted':
        return {'status': 'FEHLER', 'grund': 'EMPFAENGER_ROUTE_UNGUELTIG'}
    if route == 'vinted' and (not bot_token or not chat_id):
        return {'status': 'FEHLER', 'grund': 'VINTED_EMPFAENGER_FEHLT'}
    _m2 = None  # JACK_TUNE_MELDEREGELN N2
    if route == 'default' and quelle not in ('telegram', 'fahrdigest'):  # fahrdigest nie neu einstufen (Claude 26.10.: sonst puffert sich die Sammelmeldung selbst)
        try:
            import jack_melderegel as _mr
            _m2 = _mr.entscheide_live(text, quelle, wichtig)
            if _m2['klasse'] == 'NUR_LOG':
                try:
                    _record(HOME / 'logs' / 'telegram_nur_log.jsonl',
                            {'ts': _now(), 'quelle': quelle, 'grund': _m2['grund'],
                             'klasse': 'NUR_LOG', 'text': text[:500]},
                            max_size=MAX_LOG, rotate=True)
                except OSError as _e:
                    _audit('M2-LOGFEHLER', quelle, type(_e).__name__)
                    _m2 = None
                else:
                    return {'status': 'NUR_LOG', 'grund': _m2['grund']}
            if _m2 is not None:
                wichtig = _m2['klasse'] == 'SOFORT'
        except Exception as _e:
            _audit('M2-FEHLER', quelle, type(_e).__name__)
            _m2 = None
    if PUFFER_AKTIV and not wichtig and _buffer_during_drive():
        event = {'v': 1, 'id': uuid.uuid4().hex, 'ts': _now(), 'quelle': quelle,
                 'route': route, 'text': text, 'status': 'GEPUFFERT', 'wichtig': False}
        try:
            _record(QUEUE, event, max_size=MAX_QUEUE)
            if _m2 is not None:
                try: _mr.quittiere(_m2)
                except Exception: pass
            return {'status': 'GEPUFFERT', 'id': event['id']}
        except (OSError, ValueError) as e:
            # Nicht unbemerkt verwerfen; und NICHT bei fahrender Person ersatzweise senden.
            _audit('QUEUEFEHLER', quelle, 'QUEUE_VOLL' if str(e) == 'QUEUE_VOLL' else type(e).__name__)
            return {'status': 'FEHLER', 'grund': 'QUEUE_UNVERFUEGBAR'}
    try:
        token, target = (bot_token, chat_id) if bot_token is not None else _conf()
        if not token or not target:
            return {'status': 'FEHLER', 'grund': 'TELEGRAM_CONFIG_FEHLT'}
    except (OSError, ValueError):
        return {'status': 'FEHLER', 'grund': 'TELEGRAM_CONFIG_UNLESBAR'}
    sent, logged = 0, True
    for off in range(0, len(text), CHUNK):
        part = text[off:off + CHUNK]
        try:
            _deliver(part, token, target)
        except (OSError, ValueError, KeyError, urllib.error.HTTPError, urllib.error.URLError) as e:
            _audit('FEHLER', quelle, type(e).__name__)
            return {'status': 'TEILWEISE' if sent else 'FEHLER',
                    'teile_gesendet': sent, 'grund': 'SENDEN_FEHLGESCHLAGEN'}
        sent += 1
        try:
            # Nur nach ACK; Format Kap. 293: 3 Felder, identisch zum bestehenden Chatlog.
            _record(LOG, {'ts': _now(), 'von': 'jack', 'quelle': quelle,
                          'wichtig': wichtig, 'text': part[:2000]},
                    max_size=MAX_LOG, rotate=True)
        except OSError as e:
            _audit('LOGFEHLER', quelle, type(e).__name__)
            logged = False
    if _m2 is not None and sent:
        try: _mr.quittiere(_m2)
        except Exception: pass
    return {'status': 'GESENDET', 'teile_gesendet': sent, 'log_ok': logged}
