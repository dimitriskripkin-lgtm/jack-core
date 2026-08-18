#!/usr/bin/env python3
"""API-Budgetstand. Read-only, keine Nebenwirkungen."""
import os, sys
sys.path.insert(0, os.path.expanduser("~/jack"))
def main():
    try:
        import jack_budget
        print(jack_budget.status())
    except Exception as e:
        print("Budget nicht lesbar: " + str(e)[:120])
if __name__ == "__main__":
    main()
