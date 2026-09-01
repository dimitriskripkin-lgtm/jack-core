#!/usr/bin/env python3
"""test_core.py — Pytest Unit-Tests für JACK Core-Funktionen."""
import os, sys, pytest
J = os.path.expanduser("~/jack")
sys.path.insert(0, J)

def test_jack_log_get_logger():
    from jack_log import get_logger
    log = get_logger("test_module")
    assert log is not None
    assert log.module == "test_module"

def test_jack_log_singleton():
    from jack_log import get_logger
    a = get_logger("same_module")
    b = get_logger("same_module")
    assert a is b

def test_jack_log_writes(tmp_path, monkeypatch):
    import jack_log
    monkeypatch.setattr(jack_log, "MAIN_LOG", str(tmp_path/"test.log"))
    log = jack_log.JackLogger("test")
    log.info("Testzeile")
    content = open(str(tmp_path/"test.log")).read()
    assert "Testzeile" in content
    assert "[INFO ]" in content

def test_graph_put_and_recall():
    import jack_graph as g
    g.put_node("test_node_pytest", "fakt", {"wert": "42"})
    result = g.recall("test_node_pytest")
    assert result is not None

def test_oracle_blocks_dangerous():
    import jack_oracle as o
    assert o.is_safe("rm -rf /")[0] == False

def test_oracle_allows_safe():
    import jack_oracle as o
    assert o.is_safe("sv status jack_cortex")[0] == True

def test_log_rotation(tmp_path, monkeypatch):
    import jack_log
    logfile = str(tmp_path/"big.log")
    monkeypatch.setattr(jack_log, "MAIN_LOG", logfile)
    monkeypatch.setattr(jack_log, "MAX_LOG_BYTES", 10)
    open(logfile,'w').write("x"*20)
    jack_log._rotate_if_needed()
    assert os.path.exists(logfile+".1")
