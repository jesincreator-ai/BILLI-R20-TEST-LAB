# BILLI R-20 AI LAB

BILLI-OS AI — modular AI and robotics test lab for the future BILLI R-20 robot.

## Private Drive → Supabase → BILLI RAG

The current integration indexes text from one private Google Drive folder and all of its descendant folders into Supabase Postgres + pgvector. BILLI Chat Lab retrieves matching English, Tamil and Sinhala chunks and, when a Gemini API key is configured, generates an evidence-grounded answer with source links.

**Drive stays private.** Create a Google Cloud service account, enable the Drive API, and share only the intended BILLI folder with its service-account email as Viewer. Do not use an Anyone-with-the-link share. The application requests Drive read-only scope and never modifies source files.

### 1. Create and configure Supabase

1. Create a Supabase project at https://supabase.com/dashboard.
2. Open SQL Editor and run `supabase/migrations/202611240001_billi_drive_knowledge.sql`.
3. From Project Settings → API, copy the Project URL and the server-side Secret key. The legacy `service_role` key is accepted if your project still shows it.
4. Keep the secret key private. The migration revokes access from `anon` and `authenticated`, enables RLS, and grants private backend access to `service_role` only.

### 2. Create a read-only Drive service account

1. In Google Cloud Console, create a project and enable Google Drive API.
2. Create a service account and generate a JSON key.
3. Copy the service account email address.
4. In Google Drive, share only your private BILLI database root folder with that email as **Viewer**. Child folders/files inherit the share. Do not make the folder public.
5. Copy the folder ID from the folder URL. The application recursively reads this folder and its descendants.
6. Store the JSON key in a secret manager/Vercel environment variable; never place it in Git, the public folder, or frontend JavaScript.

### 3. Configure Vercel environment variables

Set these for Production and Preview as appropriate:

- `SUPABASE_URL` — project URL.
- `SUPABASE_SECRET_KEY` — server-side Supabase Secret key (preferred), or `SUPABASE_SERVICE_ROLE_KEY` for legacy projects.
- `GOOGLE_SERVICE_ACCOUNT_JSON` — complete service-account JSON value.
- `BILLI_DRIVE_FOLDER_ID` — private root folder ID.
- `BILLI_ADMIN_TOKEN` — long random bearer secret used to protect chat, search and sync while this is a private test app.
- `GEMINI_API_KEY` — Google AI Studio API key for embeddings and answer generation.
- `GEMINI_EMBEDDING_MODEL=gemini-embedding-2`.
- `GEMINI_CHAT_MODEL=gemini-3.8-flash`.
- `GEMINI_EMBEDDING_DIMENSIONS=768`.

Generate an admin token locally with `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Never share it in a public issue or commit.

Keep the Vercel project Root Directory as `./` (repository root). Leave Build Command and Output Directory unset. Redeploy after saving environment variables.

### 4. Connect from the BILLI dashboard

1. Open https://billi-r20.vercel.app/ and go to Settings.
2. Paste `BILLI_ADMIN_TOKEN` into the access-token field and choose Save for this tab. It is stored in `sessionStorage`, not committed or written to localStorage.
3. Open Knowledge Studio and choose Sync private Drive folder.
4. Sync runs in resumable batches (up to 10 files per request). Use Continue when the current batch finishes. Supported formats include Google Docs, Sheets and Slides exports, PDF, DOCX, XLSX, TXT, Markdown, CSV, JSON, JSONL and HTML.
5. Search the indexed knowledge or use Chat Lab. Chat answers include Drive source titles and source links when available.

### API

- `GET /health` — non-sensitive configuration status.
- `GET /api/integrations/status` — protected connectivity status.
- `POST /api/drive/sync` — protected, start a folder sync job.
- `POST /api/drive/sync/{job_id}/step` — protected, continue a batch.
- `POST /api/knowledge/search` — protected language-aware retrieval.
- `POST /api/chat` — protected RAG chat.
- `GET /docs` — FastAPI API explorer.

All private endpoints require the `X-BILLI-ADMIN-TOKEN` header. Do not remove that check on a public deployment.

## Local development (Windows PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
$env:PYTHONPATH = ".;backend"
uvicorn main:app --reload
```

Open http://127.0.0.1:8000. Run tests with:

```powershell
$env:PYTHONPATH = "backend"
python -m pip install httpx
python -m unittest discover -s backend/tests -v
```

## Important limitations and privacy notes

- No Drive content is copied into GitHub. Extracted text/chunks and metadata are written to the private Supabase project.
- The source Drive files are read-only and remain in their original folders.
- Image-only/scanned PDFs, audio/video, ZIP archives and unsupported binary formats are reported as skipped; OCR/media pipelines are not included in this increment.
- Google Workspace export and the per-file safety limit may cause large files to be skipped. The limit is controlled by `BILLI_MAX_DRIVE_FILE_MB` (default 10 MB).
- The sync endpoint is resumable and processes small batches because Vercel functions have execution limits. A very large Drive may require many Continue actions; use a background worker for future scheduled full syncs.
- Gemini answer generation and embeddings require `GEMINI_API_KEY`; with no key, the app can still use Supabase keyword retrieval and show excerpts without inventing a model answer.
- The test admin token is a single shared secret, not a multi-user login system. Replace it with Supabase Auth and role-based access before sharing the app widely.
- Vercel function filesystems are ephemeral; Supabase is the persistent knowledge store.

Never commit `.env`, OAuth/service-account JSON, API keys, Supabase secret keys, admin tokens, or imported Drive data.
