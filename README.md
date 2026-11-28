# BILLI R-20 AI LAB

BILLI-OS AI — modular AI and robotics test lab for the future BILLI R-20 robot.

## Local memory configuration

The consent-gated memory endpoints require:
- `BILLI_ADMIN_TOKEN`
- `BILLI_MEMORY_DB` writable SQLite path

Endpoints:
- `POST /api/memory/remember`
- `POST /api/memory/recall`

Memory is never stored or returned without an explicit `consent: true`. Chat can store an explicitly supplied key/value only when `memory_consent: true`, admin authentication is valid, and `BILLI_MEMORY_DB` is configured.

Hosted persistence is not claimed. Vercel filesystems are ephemeral; configure a managed persistent database before enabling hosted writes.

## Honest feature status

- Mem0 Lite: consent-gated local SQLite helper with API/chat orchestration now implemented; no automatic background memory capture.
- AI providers: not configured.
- Hardware: simulation only.
- Google Drive: not configured.
- Never commit .env files, OAuth credentials, API keys, or admin tokens.

- Multilingual response composition: deterministic English/Tamil/Sinhala phrases with script detection; no LLM translation claim.
