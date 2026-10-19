#!/usr/bin/env python3
"""Proposed JACK_TUNE_WLGUARD2: verify single registry wiring without imports.

This is a static *consistency* check, NOT a runtime authorization audit.
Source of truth: jack_acts.ACTs; runner and MCP must both refer to _acts.names().
"""
import ast
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parent


def _assigned_name(node, name):
    if not isinstance(node, (ast.Assign, ast.AnnAssign)):
        return False
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    return any(isinstance(t, ast.Name) and t.id == name for t in targets)


def registry(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    candidates = [n for n in tree.body if _assigned_name(n, "ACTS")]
    if len(candidates) != 1:
        raise ValueError("jack_acts.ACTs missing or ambiguous")
    acts = ast.literal_eval(candidates[0].value)
    if not isinstance(acts, dict) or not acts:
        raise ValueError("ACTS missing or empty")
    for name, spec in acts.items():
        if not isinstance(name, str) or not isinstance(spec, dict):
            raise ValueError("invalid ACTS entry")
        if type(spec.get("freigabe")) is not bool or type(spec.get("xiaomi")) is not bool:
            raise ValueError("invalid ACTS flags: " + name)
    names_functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "names"]
    if len(names_functions) != 1 or len(names_functions[0].body) != 1:
        raise ValueError("names() missing or ambiguous")
    expr = names_functions[0].body[0]
    # Strongly constrain the name helper to 'return sorted(ACTS)'
    good_names = (isinstance(expr, ast.Return) and isinstance(expr.value, ast.Call)
                  and isinstance(expr.value.func, ast.Name) and expr.value.func.id == "sorted"
                  and len(expr.value.args) == 1 and isinstance(expr.value.args[0], ast.Name)
                  and expr.value.args[0].id == "ACTS")
    if not good_names:
        raise ValueError("names() no longer directly reflects ACTS")
    return acts


def uses_registry(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    assignments = [n for n in ast.walk(tree) if _assigned_name(n, "ALLOWED")]
    imports = [alias for n in ast.walk(tree) if isinstance(n, ast.Import)
               for alias in n.names if alias.name == "jack_acts" and alias.asname == "_acts"]
    if len(assignments) != 1 or not imports:
        return False
    val = assignments[0].value
    return (isinstance(val, ast.Call) and isinstance(val.func, ast.Name)
            and val.func.id == "set" and len(val.args) == 1 and not val.keywords
            and isinstance(val.args[0], ast.Call) and not val.args[0].args
            and not val.args[0].keywords and isinstance(val.args[0].func, ast.Attribute)
            and val.args[0].func.attr == "names"
            and isinstance(val.args[0].func.value, ast.Name)
            and val.args[0].func.value.id == "_acts")


def verify(home):
    acts = registry(home / "jack_acts.py")
    for name in ("jack_mission_runner.py", "jack_mcp_server.py"):
        if not uses_registry(home / name):
            return False, name + " does not use a single _acts.names() registry"
    return True, "single registry: %d acts; static wiring only" % len(acts)


def main():
    try:
        ok, note = verify(HOME)
        print("WLGUARD %s: %s" % ("OK" if ok else "FAIL", note))
        return 0 if ok else 1
    except (OSError, SyntaxError, ValueError, TypeError) as exc:
        print("WLGUARD FAIL: %s: %s" % (type(exc).__name__, str(exc)[:180]))
        return 2


if __name__ == "__main__":
    sys.exit(main())
