# BILLI R-20 Unified Antigravity Workspace (Option A)

## Purpose
One Antigravity workspace coordinates existing repositories without merging Git histories. Each component remains an independent Git repository to preserve branches, PRs, licenses and module boundaries.

## Status / limitations
- Setup scaffold committed in BILLI-R20-TEST-LAB.
- Antigravity is a desktop app; this connector session cannot install it or open a workspace on your PC.
- Google Drive is not connected as a read/write connector here. Install Drive for desktop or approved Drive MCP and use its local sync folder.
- Dropbox contents were inspected online. Local Dropbox sync path is required for offline ingestion.
- Database ingestion, deduplication and ESP32 exports are not complete; these are output locations.
- Robot runtime is designed offline. Web/backend testing is on PC/local network; hosted tests require Internet and credentials.

## Setup
1. Install Antigravity on PC and create `BILLI-R20-UNIFIED`.
2. Copy this scaffold from `docs/workspace` into the workspace root.
3. Run bootstrap: Windows `powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap_workspace.ps1`.
4. Open workspace root in Antigravity and add `AGENTS.md` to context.
5. Set `BILLI_DROPBOX_SYNC` to the Dropbox synced path containing `BILLI_R20`; set `BILLI_GOOGLE_DRIVE_SYNC` to Drive synced folder if available.
6. Implement local DB ingestion with provenance, permission/license metadata, language, date and content-hash dedupe. Avoid committing private/copyrighted text.
7. Run AI-LAB FastAPI and test local browser: health, EN/TA/SI, FTS, offline fallback, source metadata, import/export, responsive layout and error states.

## Layout
```
BILLI-R20-UNIFIED/
  AGENTS.md  workspace.json  scripts/
  repos/ (M5, M6, M7, M8, AI-LAB, WAKE, MEMORY, INTENT)
  database/ (source_records, master.sqlite3, exports/en-ta-si, esp32)
  web-tests/  local-sync/
```

## Safety / Git
- Preserve repo history; no force merges or mass changes.
- Never commit secrets, private data or unlicensed content.
- M7/M8 changes require hardware/safety tests and review.
- M6 is face/display only; no direct servo control.
- Device knowledge shards must be compact and license-cleared.
- Cloud features optional; robot must work without Wi-Fi.