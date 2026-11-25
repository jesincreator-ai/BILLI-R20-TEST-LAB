# BILLI R-20 Antigravity Workspace Rules

- Keep component repositories separate; preserve histories.
- M5 owns voice/audio. M6 owns face/display only. M7 owns servo/motion. M8 owns safety/recovery.
- Never bypass M8 safety or change servo limits without tests and review.
- Robot runtime must work offline; cloud/Drive/Supabase are optional sync/web-test services.
- ESP32-WROOM-32 has no PSRAM: avoid full framebuffers, heavy DB engines, large models and unbounded allocations.
- Master knowledge DB is PC/server SQLite+FTS5; device gets compact license-cleared JSONL/text shards on SD.
- Keep source metadata: source id/title/url/file ref, language (en/ta/si), hash, date, license/permission and confidence.
- Never add secrets, private data, copyrighted books or unlicensed full-text dumps to public repos.
- Do not merge Git histories. Treat repos as independent workspace modules.
- Inspect repo/branch/docs/tests before edits; commit small; run tests; report hardware checks not performed.
- Online tests may use FastAPI/Supabase; offline mode must have local fallback.