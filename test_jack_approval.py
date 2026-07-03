#!/usr/bin/env python3
import os
from jack_approval import check_approval, is_safe_path


def test_neue_datei_wird_automatisch_freigegeben():
    path = os.path.expanduser("~/jack/_pytest_dummy_neu.py")
    ok, reason = check_approval(path, operation="create")
    assert ok is True
    assert "Neue Datei" in reason


def test_autonom_praefix_erlaubt_edit_bestehender_datei():
    path = os.path.expanduser("~/jack/_pytest_dummy_bestehend.py")
    ok, reason = check_approval(path, operation="edit", raw_command="JACK autonom: mach das")
    assert ok is True
    assert "Autonom-Praefix" in reason


def test_forbidden_pfad_wird_blockiert():
    ok, reason = check_approval("/system/build.prop", operation="edit")
    assert ok is False
    assert "Forbidden" in reason


def test_edit_ohne_praefix_fragt_interaktiv(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "nein")
    path = os.path.expanduser("~/jack/_pytest_dummy_bestehend.py")
    ok, reason = check_approval(path, operation="edit", raw_command="ohne praefix")
    assert ok is False


def test_is_safe_path_erkennt_eigenen_jack_ordner():
    # Regressionstest fuer den Bug vom 2026-07-03:
    # /data/data/ als Forbidden-Regel blockte faelschlich den eigenen ~/jack Ordner
    path = os.path.expanduser("~/jack/irgendwas.py")
    safe, reason = is_safe_path(path)
    assert safe is True


def test_is_safe_path_blockt_fremde_data_data_pfade():
    safe, reason = is_safe_path("/data/data/com.other.app/files/secret.db")
    assert safe is False
