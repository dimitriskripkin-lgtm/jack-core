# 258 Skill-Ideen aus erledigter Arbeit (/skillideen)

jack_skillidee.py (JACK_TUNE_SKILLIDEE). Telegram /skillideen. Hermes-Idee, aber nur als Vorschlag.
- Liest missions/logs der letzten 30 Tage, teilt sie in Arbeitsfolgen (Pause > 10 min = neue Folge) und zaehlt wiederkehrende, durchgehend erfolgreiche Act-Abfolgen (3 bis 5 Schritte, mindestens 3 verschiedene Acts, reine Pruefungen zaehlen kaum). Kein LLM, 0,7 s.
- Erster Lauf 09.10.: py_replace > compile_ok > sv_restart (34x), compile_ok > sv_restart > sv_ok (11x), py_replace > ro_scan > git_publish (10x). Das ist der Patch-Zyklus: Kandidat fuer einen Skill 'patch_und_pruefen' (batch aus Patch, Compile, Neustart, sv_ok, Scan).
- Erzeugt keinen Code und speichert keinen Skill. Naechster Schritt wuerde sein: Skill bauen, Haliza-Pruefung, Dima-Freigabe (/skill_confirm). run_skill fuehrt Code per exec aus, deshalb nie ohne Freigabe.
