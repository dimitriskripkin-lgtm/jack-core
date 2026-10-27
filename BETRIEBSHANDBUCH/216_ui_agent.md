# 216. jack_ui_agent.py

Gelesen 03.10.2026, Kopf. Kein Umbau.

**Zweck:** import subprocess,os,time,sys sys.path.insert(0,os.path.expanduser('~/jack'))


**Stand 15.10.2026:** Sicherheitsumbau AGENTSAFE, siehe Kapitel 283.

**Nachtrag 26.10.2026 (Claude, K1b von ChatGPT)**
JACK_TUNE_XIGATE_UI/_TERMUX: _ssh und _termux_cmd laufen ueber jack_xiaomi.run_shell(as_root=False) mit Breaker. Rueckgabe kompatibel (CompletedProcess bzw. Text). Live vorher/nachher identisch: echo ok 0.1 s.

**Nachtrag 27.10.2026:** run_agent-Wrapper prueft start_app gegen jack_app_sperre vor Unlock (K1c-P2), siehe Kap 296.
