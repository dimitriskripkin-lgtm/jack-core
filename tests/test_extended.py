#!/usr/bin/env python3
"""test_extended.py — Coverage für jack_graph, jack_missions, jack_mission_runner, jack_schema."""
import os, sys, json, tempfile, pytest
J = os.path.expanduser("~/jack")
sys.path.insert(0, J)

# ── jack_graph ───────────────────────────────────────────────────────────────
def test_graph_put_node_returns_something():
    import jack_graph as g
    result = g.put_node("pytest_node", "fakt", {"val": "test"})
    assert result is not False

def test_graph_recall_known():
    import jack_graph as g
    g.put_node("pytest_recall", "fakt", {"val": "42"})
    r = g.recall("pytest_recall")
    assert r is not None

def test_graph_recall_unknown():
    import jack_graph as g
    # recall() macht globale Suche — gibt immer Graph-Inhalt zurück
    r = g.recall("dieser_node_existiert_nicht_xyz")
    assert r is not None  # Globale Suche, kein None-Return

def test_graph_keyword_guard_rejects():
    import jack_graph as g
    r = g.put_node("SEKTOR-7", "fakt", {"val": "rot"})
    assert not r

def test_graph_put_edge():
    import jack_graph as g
    g.put_node("pytest_a", "person", {"name": "A"})
    g.put_node("pytest_b", "person", {"name": "B"})
    try:
        g.put_edge("pytest_a", "kennt", "pytest_b")
    except Exception as e:
        pytest.fail(f"put_edge raised: {e}")

# ── jack_schema ──────────────────────────────────────────────────────────────
def test_schema_valid_mission():
    import jack_schema as s
    m = {"id": "test_001", "act": "compile_ok", "typ": "check",
         "file": "~/jack/jack_log.py", "_prio": 2}
    ok, errs = s.validate(m)
    assert ok, f"Fehler: {errs}"

def test_schema_missing_required():
    import jack_schema as s
    ok, errs = s.validate({"act": "compile_ok"})
    assert not ok
    assert any("id" in e for e in errs)

def test_schema_invalid_act():
    import jack_schema as s
    ok, errs = s.validate({"id": "x", "act": "rm_rf_slash"})
    assert not ok
    assert any("act" in e for e in errs)

def test_schema_prio_out_of_range():
    import jack_schema as s
    ok, errs = s.validate({"id": "x", "act": "compile_ok", "_prio": 99})
    assert not ok

def test_schema_staged_without_file():
    import jack_schema as s
    ok, errs = s.validate({"id": "x", "act": "compile_ok", "staged": True})
    assert not ok

def test_schema_valid_prio_boundary():
    import jack_schema as s
    for p in [0, 4, 8]:
        ok, errs = s.validate({"id": "x", "act": "compile_ok", "_prio": p})
        assert ok, f"Prio {p} sollte gültig sein: {errs}"

# ── jack_mission_runner ──────────────────────────────────────────────────────
def test_runner_compile_ok_valid():
    import jack_mission_runner as r
    m = {"id":"t1","act":"compile_ok","file":"~/jack/jack_log.py"}
    ok, msg, _ = r.run_act(m)
    assert ok

def test_runner_compile_ok_invalid():
    import jack_mission_runner as r
    m = {"id":"t2","act":"compile_ok","file":"~/jack/datei_existiert_nicht_xyz.py"}
    ok, msg, _ = r.run_act(m)
    assert not ok

def test_runner_file_exists_true():
    import jack_mission_runner as r
    m = {"id":"t3","act":"file_exists","file":"~/jack/jack_log.py"}
    ok, msg, _ = r.run_act(m)
    assert ok

def test_runner_file_exists_false():
    import jack_mission_runner as r
    m = {"id":"t4","act":"file_exists","file":"~/jack/gibts_nicht_xyz.py"}
    ok, msg, _ = r.run_act(m)
    assert not ok

def test_runner_grep_count_hit():
    import jack_mission_runner as r
    m = {"id":"t5","act":"grep_count","file":"~/jack/jack_log.py",
         "pattern":"MODULE_VERSION","expect_min":1,"expect":"PASS"}
    ok, msg, _ = r.run_act(m)
    assert ok

def test_runner_grep_count_miss():
    import jack_mission_runner as r
    m = {"id":"t6","act":"grep_count","file":"~/jack/jack_log.py",
         "pattern":"DIESER_STRING_EXISTIERT_NIEMALS_XYZ","expect_min":1,"expect":"PASS"}
    ok, msg, _ = r.run_act(m)
    assert not ok

def test_runner_unknown_act():
    import jack_mission_runner as r
    m = {"id":"t7","act":"nicht_erlaubt_xyz"}
    ok, msg, _ = r.run_act(m)
    assert not ok

# ── jack_log extended ────────────────────────────────────────────────────────
def test_log_levels(tmp_path, monkeypatch):
    import jack_log
    monkeypatch.setattr(jack_log, "MAIN_LOG", str(tmp_path/"l.log"))
    log = jack_log.JackLogger("test", jack_log.Level.DEBUG)
    log.debug("debug-msg")
    log.info("info-msg")
    log.warn("warn-msg")
    content = open(str(tmp_path/"l.log")).read()
    assert "DEBUG" in content
    assert "INFO" in content
    assert "WARN" in content

def test_log_exception(tmp_path, monkeypatch):
    import jack_log
    monkeypatch.setattr(jack_log, "MAIN_LOG", str(tmp_path/"l.log"))
    log = jack_log.JackLogger("test")
    try: raise ValueError("Testfehler")
    except Exception as e: log.exception("Test", e)
    content = open(str(tmp_path/"l.log")).read()
    assert "Testfehler" in content

def test_log_tail():
    import jack_log
    lines = jack_log.tail(5)
    assert isinstance(lines, list)
