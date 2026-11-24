# Supabase + Private Drive RAG Implementation Plan

> **For agentic workers:** execute task-by-task with tests and verification.

**Goal:** Add private, resumable Google Drive ingestion into Supabase pgvector and connect grounded multilingual retrieval to BILLI chat on Vercel.

**Architecture:** Root FastAPI remains the only app entrypoint. A Google service account reads one configured Drive folder; a Supabase REST repository stores source metadata, chunks, embeddings and sync-job state; Gemini creates embeddings and grounded answers. A server-only access token protects the private knowledge API during testing.

**Tech Stack:** Python 3.12, FastAPI, Google Drive API v3 + google-auth, Gemini API (`google-genai`), Supabase PostgREST + pgvector, SQL migrations, vanilla HTML/CSS/JS.

**Spec:** `docs/superpowers/specs/2026-11-24-supabase-drive-rag-design.md`

## Global Constraints
- Scan only `BILLI_DRIVE_FOLDER_ID` and its descendants.
- Drive permissions are read-only; never mutate or publish Drive files.
- Never commit private keys, service-role keys, API keys, access tokens, or imported Drive contents.
- Require `BILLI_ADMIN_TOKEN` for knowledge chat/search and sync endpoints.
- Use 768-dimensional embeddings consistently for documents and queries.
- Supabase tables and RPCs are private to the backend service role.
- No persistent writes to the Vercel function filesystem.

## Review Focus
- Missing/invalid environment variables → health says not configured; protected operations fail closed.
- Expired or inaccessible Google service-account credentials → sync returns a safe configuration error without exposing credentials.
- Nested folders and Drive pagination → job queue resumes without skipping pages or repeating completed files.
- Changed or unsupported Drive content → unchanged files skip; changed files replace prior chunks atomically; unsupported files are reported.
- Tamil/Sinhala or mixed-language inputs → script detector selects `ta`/`si`/`en` and language filters remain explicit.

## Files and responsibilities
- `backend/billi/security.py`: constant-time admin-token check.
- `backend/billi/language.py`, `chunking.py`, `extractors.py`: multilingual preparation and file parsing.
- `backend/billi/embeddings.py`: Gemini document/query embeddings and answer generation.
- `backend/billi/supabase_store.py`: private PostgREST operations and vector RPC calls.
- `backend/billi/drive.py`: scoped read-only Drive API client.
- `backend/billi/drive_sync.py`: resumable recursive sync jobs and per-file indexing.
- `backend/billi/rag.py`: retrieval plus grounded answer/source packaging.
- `backend/billi/api.py`: health, integration status, protected chat/search/sync endpoints.
- `supabase/migrations/202611240001_billi_drive_knowledge.sql`: private schema, pgvector, RLS, RPCs and atomic replacement function.
- `public/index.html`, `public/app.js`, `public/styles.css`: token entry, Drive sync, knowledge search, source citations and live status.
- `backend/tests/`: unit and API regression tests.

## Tasks

### Task 1 — Core security and document preparation
- [ ] Add tests for constant-time token match behavior, language detection, chunk overlap and text extraction.
- [ ] Run tests and verify they fail for missing modules/behavior.
- [ ] Implement `security.py`, `language.py`, `chunking.py`, `extractors.py`.
- [ ] Run the focused and full Python test suites.

### Task 2 — Persistent Supabase and Gemini adapters
- [ ] Add tests for vector serialization, RPC call shape and no-answer-without-evidence behavior.
- [ ] Implement the Supabase REST repository and Gemini Embedding 2 / Gemini 3.8 Flash adapters.
- [ ] Add the SQL migration with pgvector, RLS, private grants, vector/keyword search RPCs and atomic file replacement.
- [ ] Run tests and SQL static checks.

### Task 3 — Private Drive ingestion
- [ ] Add tests for recursive folders, paging, unchanged-file skipping and resumable job state.
- [ ] Implement service-account read-only Drive API and MIME-aware text extraction.
- [ ] Implement resumable per-request import jobs and source metadata.
- [ ] Run tests with fake Drive/Supabase adapters; no live Drive access until credentials are configured.

### Task 4 — Grounded API and dashboard
- [ ] Add API tests proving knowledge endpoints reject missing/incorrect tokens.
- [ ] Replace demo-only chat behavior with evidence-grounded retrieval and Gemini response generation; return source references.
- [ ] Add protected status/search/sync endpoints.
- [ ] Add session-only token UI, sync progress, search results and cited chat sources.
- [ ] Run the full backend suite and JavaScript syntax checks.

### Task 5 — Deploy readiness
- [ ] Update root dependency declarations and CI workflow.
- [ ] Confirm Vercel root entrypoint, API/static route behavior and no secrets in tracked files.
- [ ] Push commit and verify GitHub Actions.
- [ ] Verify the live Vercel app health and new endpoints; report external credentials/setup that remain.

## Execution notes
Use fake Drive and Supabase adapters in tests. A test suite cannot prove the user's external cloud credentials, service-account sharing, database migration, or Vercel environment variables are valid; those require the user's connected project and authorized private folder.