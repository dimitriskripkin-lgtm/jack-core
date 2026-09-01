#!/usr/bin/env python3
"""test_core.py — Pytest Unit-Tests für JACK Core-Funktionen."""
import os, sys, json, tempfile, pytest
J = os.path.expanduser("~/jack")
sys.path.insert(0, J)

# jack_log
def test_jack_log_get_logger():
    from jack_log import get_logger, Level
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

# jack_graph
def test_graph_put_and_recall():
    import jack_graph as g
    g.put_node("test_node_pytest", "fakt", {"wert": "42"})
    result = g.recall("test_node_pytest")
    assert result is not None

def test_graph_keyword_guard():
    import jack_graph as g
    # Groq-Halluzination sollte abgelehnt werden
    result = g.put_node("SEKTOR-7", "fakt", {"wert": "rot"})
    assert result is None or result == False

# jack_config
def test_config_loads():
    import jack_config as c
    assert c is not None

def test_config_jack_home():
    import jack_config as c
    home = c.get("JACK_HOME", fallback=None) or os.path.expanduser("~/jack")
    assert os.path.exists(home)

# jack_oracle
def test_oracle_blocks_dangerous():
    import jack_oracle as o
    assert o.is_safe("rm -rf /") == False
    assert o.is_safe("format") == False

def test_oracle_allows_safe():
    import jack_oracle as o
    assert o.is_safe("sv status jack_cortex") == True

# jack_selftest
def test_selftest_runs():
    import jack_selftest as s
    result = s.run_all()
    assert "score" in result
    assert result["score"] >= 0

# jack_log rotation
def test_log_rotation(tmp_path, monkeypatch):
    import jack_log
    logfile = str(tmp_path/"big.log")
    monkeypatch.setattr(jack_log, "MAIN_LOG", logfile)
    monkeypatch.setattr(jack_log, "MAX_LOG_BYTES", 10)
    open(logfile,'w').write("x"*20)
    jack_log._rotate_if_needed()
    assert os.path.exists(logfile+".1")
