# BILLI R-20 AI LAB

BILLI-OS AI — modular AI and robotics test lab for the future BILLI R-20 robot.

## Deploy on Vercel

This repository uses one root-level FastAPI entrypoint: main.py exports the app from backend.billi.api. Root pyproject.toml and requirements.txt hold Python deployment configuration. Browser assets are under public/ and are served as static files.

Set Vercel Root Directory to the repository root (./). Leave Build Command and Output Directory unset; Vercel should detect the Python FastAPI app. Redeploy the latest main commit.

API health check: /health. Chat endpoint: POST /api/chat. FastAPI API explorer: /docs.

## Local development (Windows PowerShell)

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PYTHONPATH = "."
uvicorn main:app --reload

Open http://127.0.0.1:8000.

Tests: install httpx, set PYTHONPATH=backend, then run python -m unittest discover -s backend/tests -v.

## Honest feature status

- Nanobot Lite: deterministic intent router, not an LLM.
- Mem0 Lite: consent-gated local SQLite helper; not automatically connected to conversations.
- Knowledge/RAG database: not configured in this deployment starter.
- Local and external model providers: not configured.
- Wake Lite: no wake-word detector configured.
- Voice Lite: browser capabilities only; support varies.
- Robot face and hardware: visual preview/simulation only; no physical ESP32 is connected.
- Google Drive: private connector not configured; no Drive files are read or exposed.

## Vercel storage warning

Vercel function filesystems are ephemeral. Do not rely on a SQLite file in the function runtime as durable storage. Add a persistent managed database before enabling hosted knowledge or memory writes.

Never commit .env files, OAuth credentials, API keys, or admin tokens.\n\n## Phase 2 progress\n\nA local-first `backend/billi/knowledge.py` module now provides SQLite + FTS5 indexing, English/Tamil/Sinhala language validation, upsert/search, and JSONL export. It is intentionally not enabled as hosted persistence yet; the next task is wiring it into the authenticated knowledge API and adding explicit import/export commands.\n

## BILLI Unified Antigravity Workspace (Option A)

Workspace scaffold and setup instructions are available in [`docs/workspace/SETUP.md`](docs/workspace/SETUP.md). The repository manifest is [`docs/workspace/workspace.json`](docs/workspace/workspace.json), project rules are [`docs/workspace/AGENTS.md`](docs/workspace/AGENTS.md), and Windows bootstrap script is [`docs/workspace/scripts/bootstrap_workspace.ps1`](docs/workspace/scripts/bootstrap_workspace.ps1). This setup preserves separate Git repositories.
