# BILLI R-20 AI LAB

BILLI-OS AI — modular robotics AI development and testing lab for the future BILLI R-20 robot.

**Status:** Frontend foundation plus backend starter. The API, deterministic intent routing, and consent-gated local-memory module are implemented. The AI provider, knowledge database, physical hardware, and actual 3D face are not connected. Demo responses are clearly labeled and are not LLM output.

## Frontend
Open `index.html` in a browser or serve the repository using `python -m http.server 8000`.

Includes responsive command center, CALM/RUGGED preview, expression controls, demo chat, knowledge search empty state, voice browser capability UI, hardware simulator UI, and diagnostics.

## Backend starter
See [ROADMAP.md](ROADMAP.md) for phase progress and setup.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn billi.api:app --app-dir backend --reload
```
API docs: `http://127.0.0.1:8000/docs`; health: `http://127.0.0.1:8000/health`.

Tests:
```bash
python -m unittest discover -s backend/tests -v
```

## Planned architecture
FastAPI → Nanobot Lite intent router → orchestration adapters → local model/provider (future), Mem0 Lite consent-gated local memory, SQLite/FTS5 RAG and JSONL tools, Wake Lite/Voice Lite, face animation, hardware simulation/MicroPython, private Drive OAuth, and QA.

Languages planned: English, Tamil, Sinhala. Security: no credentials or private Drive connection committed. Hardware is simulation only until physically validated.

See [ROADMAP.md](ROADMAP.md) for phases, verification status, and blockers.
