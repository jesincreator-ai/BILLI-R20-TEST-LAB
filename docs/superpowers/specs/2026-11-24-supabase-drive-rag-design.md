# BILLI R-20 private Drive + Supabase knowledge design

## Intent
Connect the live BILLI R-20 Vercel app to a private Google Drive knowledge folder and persistent Supabase Postgres/pgvector store. Import all supported files recursively from one configured folder, preserve source attribution, and answer English, Tamil and Sinhala questions with retrieved source evidence.

## User outcome
The owner can authorize a private Drive folder, run a resumable import, search indexed documents, and chat with BILLI using evidence retrieved from that index. The original Drive files remain unchanged and are not made public.

## Selected approach
- Drive access: Google Cloud service account using Drive API v3 read-only scope. The owner shares only the target BILLI folder with the generated service-account address as Viewer. This avoids broad user-drive OAuth consent and does not publish the folder.
- Persistent knowledge store: Supabase Postgres with pgvector. A private source table records Drive metadata and a chunk table stores extracted text, language, provenance and 768-dimensional vectors. An RPC performs vector search and a keyword fallback.
- Embeddings and response generation: Gemini Embedding 2 (`gemini-embedding-2`, 768 dimensions) and Gemini 3.8 Flash (`gemini-3.8-flash`). Model IDs remain configurable environment variables.
- Deployment: existing root FastAPI app on Vercel; all credentials stay in server-side environment variables. Imports run in small resumable batches to respect serverless request limits.
- Access control: one high-entropy BILLI admin/access token gates chat, search and Drive sync while this is a private test app. The token is entered in the dashboard and kept in sessionStorage for that tab only. Replace this with Supabase Auth before multi-user production.

## Data flow
Google Drive folder (read-only service account) → recursive metadata scan → content export/download → MIME-aware text extraction → language detection and overlapping chunks → Gemini embeddings → atomic Supabase chunk replacement → vector retrieval → grounded Gemini answer with source references.

## Data and security boundaries
- Only one configured Drive folder ID and its descendants are scanned.
- Drive files are read, never edited, moved, deleted or re-shared.
- The Drive folder and indexed Supabase tables are not public.
- Supabase service-role/secret key, Google service-account JSON, Gemini API key and BILLI token are server-only secrets; none belong in Git or browser code.
- All public/anon/authenticated access to private knowledge tables and RPCs is revoked; the FastAPI backend uses the Supabase secret key.
- Unsupported files and files over the configured size limit are reported as skipped, not silently treated as indexed.
- Vercel local filesystem is not used for permanent data; Supabase is authoritative.

## Non-goals
Physical robot control, automated deletion of stale Drive records, multi-user identity/roles, and binary/media understanding are not part of this integration increment.

## Operational limits
Drive exports of Google Workspace files are subject to Google's export-size constraints. Each Vercel sync request indexes only a bounded number of files and persists a resumable queue. A full large-folder import may require multiple Continue actions or a later background worker.

## Remaining setup outside code
Create a Supabase project and apply the migration; create a Google Cloud service account with Drive API enabled; share the private folder to its email as Viewer; set the Vercel environment variables; provide the folder ID. No account credentials are embedded in the repository.