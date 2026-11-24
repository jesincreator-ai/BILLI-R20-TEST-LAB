# BILLI R-20 Roadmap

## Deployment foundation
- [x] Root FastAPI entrypoint (`main.py`)
- [x] Root Python dependencies and Python 3.12 pin
- [x] Static web assets under `public/`
- [x] Vercel project configuration
- [x] CI workflow for backend tests
- [ ] Verify first Vercel deployment in the user's Vercel account

## Knowledge integration
- [x] Private Supabase schema with pgvector, RLS and backend-only RPC grants
- [x] Google Drive read-only service-account adapter scoped to one configured folder
- [x] Recursive, paginated and resumable Drive sync jobs
- [x] Text extraction for common documents and metadata/provenance retention
- [x] English, Tamil and Sinhala script detection and chunk metadata
- [x] Gemini Embedding 2 adapter (768 dimensions)
- [x] Grounded Gemini 3.8 Flash answer adapter and source references
- [x] Protected private chat, knowledge search and Drive sync API routes
- [x] Dashboard token, sync and search controls
- [ ] Apply migration to the user's Supabase project
- [ ] Configure Supabase, Drive service-account and Gemini secrets in Vercel
- [ ] Share the target Drive folder privately to the service-account address
- [ ] Run the first real folder import and validate multilingual retrieval
- [ ] Replace the single admin test token with Supabase Auth before multi-user access

## Other application modules
- [x] Deterministic Nanobot Lite intent router (starter)
- [x] Consent-gated Mem0 Lite SQLite helper (starter)
- [x] CALM / RUGGED visual mode preview
- [x] Expression control preview
- [x] Browser voice capability detection
- [x] ESP32 hardware simulator view
- [ ] Physical ESP32 firmware integration and hardware validation
- [ ] Reference-matched 3D face model and animation
- [ ] Google Drive change-notification/webhook sync
- [ ] OCR for scanned PDFs and image documents

## Safety / status rules

Never treat a demo response as an LLM answer. Private knowledge endpoints require the server-side admin token. Supabase knowledge tables are inaccessible to public/anon/authenticated roles. Drive is read-only and folder-scoped; source files are never moved or modified. A missing or unsupported file is reported as skipped. Vercel filesystem data is ephemeral; use Supabase for persistent records.
