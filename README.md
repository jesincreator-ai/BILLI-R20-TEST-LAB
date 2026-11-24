# BILLI R-20 AI LAB

BILLI-OS AI — modular robotics AI development and testing lab for the future BILLI R-20 robot.

**Status:** Foundation UI. Backend, SQLite database, model providers, true 3D face, and physical hardware are not connected. Demo chat labels its output honestly.

## Run
Open `index.html` in a browser, or use `python -m http.server 8000` then visit http://localhost:8000.

## Foundation UI features
- Responsive navigation / command center
- CALM and RUGGED face theme switching
- Eight expression previews
- Demo chat UI (no real AI claim)
- Knowledge empty-state/search UI
- Four AI system overview
- Browser speech capability checks and speech synthesis
- Hardware simulator UI
- Diagnostics status

## Planned phases
1. Frontend foundation
2. FastAPI backend, Nanobot Lite, Mem0 Lite, Wake Lite/Voice Lite adapters, orchestrator
3. SQLite + FTS5 RAG and JSONL, evidence-backed search
4. Reference-based 3D robot face
5. Voice and memory integration
6. Hardware simulation + MicroPython interfaces
7. Private Google Drive OAuth connector foundation
8. ESP32 export tools
9. QA and testing

Languages targeted: English (en), Tamil (ta), Sinhala (si). Full localized UI and multilingual RAG are future work.

Security: No credentials or private Drive connection included. Do not commit secrets.

Design based on the three BILLI R-20 images supplied in the project PDF. Image assets themselves are not yet checked into this repository.
