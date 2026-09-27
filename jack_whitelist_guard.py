#!/usr/bin/env python3
# JACK_TUNE_WLGUARD - prueft ob beide ALLOWED-Whitelists synchron sind
import re, sys

RUNNER = "/data/data/com.termux/files/home/jack/jack_mission_runner.py"
MCPSRV = "/data/data/com.termux/files/home/jack/jack_mcp_server.py"

def extract_allowed(path, pattern):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.search(pattern, text, re.S)
    if not m:
        return None
    raw = m.group(1)
    return set(re.findall(r'"([a-zA-Z_][a-zA-Z0-9_]*)"', raw))

runner_set = extract_allowed(RUNNER, r"ALLOWED\s*=\s*set\(\[(.*?)\]\)")
mcp_set    = extract_allowed(MCPSRV, r"ALLOWED\s*=\s*\{(.*?)\}")

if runner_set is None or mcp_set is None:
    print("WLGUARD: konnte eine der beiden Listen nicht finden - manuell pruefen!")
    sys.exit(2)

only_runner = runner_set - mcp_set
only_mcp    = mcp_set - runner_set

if not only_runner and not only_mcp:
    print("WLGUARD OK: beide Whitelists synchron (" + str(len(runner_set)) + " Acts)")
    sys.exit(0)
else:
    print("WLGUARD MISMATCH!")
    if only_runner:
        print("  Nur im Runner, fehlt im MCP-Server: " + ", ".join(sorted(only_runner)))
    if only_mcp:
        print("  Nur im MCP-Server, fehlt im Runner: " + ", ".join(sorted(only_mcp)))
    sys.exit(1)
