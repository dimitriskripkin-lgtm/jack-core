# 290 mobile-use (Minitap) als Haende B, Installation 20.10.2026
- Paket minitap-mobile-use 4.0.0 (Apache-2.0, github.com/minitap-ai/mobile-use), abgetrennt in ~/jack_ext/mobile_use (venv mit --system-site-packages, 91 MB+). JACK-Dienste unberuehrt.
- Termux-Haken: Python 3.14, langchain-cerebras nicht verfuegbar (nur in Tests benutzt, weggelassen), psutil/lxml per apt (python-psutil, python-lxml), iOS-Modul idb sowie langchain_google_vertexai und langchain_azure_ai als Stubs (werfen RuntimeError bei Benutzung).
- Telemetrie: immer mit MOBILE_USE_TELEMETRY_ENABLED=false starten (sonst PostHog).
- ADB zum Xiaomi steht: 172.29.165.131:5555 device.
- Import-Test OK (sdk.Agent, Builders). Noch KEIN Lauf am Geraet: erst Adapter jack_actor_b mit JACK-Waechter (Auftrag 12 ChatGPT), dann Arena E als Vergleich.
