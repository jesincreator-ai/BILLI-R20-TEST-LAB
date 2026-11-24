# BILLI R-20 Drive → Supabase private knowledge integration
## 1. Create Supabase project
Run `migrations/001_billi_drive_knowledge.sql` in Supabase SQL Editor. Keep the project private and do not enable public RLS policies.
## 2. Vercel server environment variables
Set these in Vercel Project → Settings → Environment Variables (Production and Preview as appropriate):
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY` (server-only; never expose to browser)
- `GEMINI_API_KEY` (server-side only, embedding calls)
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI=https://billi-r20.vercel.app/api/drive/oauth/callback`
- `BILLI_TOKEN_ENCRYPTION_KEY` (generate using `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`)
- `BILLI_ADMIN_TOKEN` (long random secret for starting a sync; do not put in frontend)
## 3. Google OAuth
Create a Google Cloud OAuth Web client. Add redirect URI above. Configure OAuth consent screen and grant Drive read-only scope. The integration only reads file contents; it never edits files, moves them, changes permissions, or deletes them. Drive folder/file privacy and sharing are preserved.
## 4. First connection
Visit `https://billi-r20.vercel.app/api/drive/oauth/start`, sign in with the Drive owner account, consent to read-only access. Callback stores refresh credentials encrypted in Supabase. Sync is a backend endpoint protected by admin token; call it using Authorization: Bearer <BILLI_ADMIN_TOKEN>.
## 5. Import limitations
Initial full sync lists all accessible non-trashed files. Private search endpoints are protected by the admin bearer token (Knowledge Studio asks for it in the sync-token field). OAuth state is validated with a secure, HttpOnly cookie. Extractable types: Google Docs (text export), Sheets (CSV), text files, PDFs. Unsupported types (images, audio/video, binary Office) are counted as skipped; OCR can be added later. Text is embedded using the current multilingual Gemini embedding model with 768 dimensions and stored in Supabase vector chunks with source file metadata. Drive source links remain private, and returned citations point to source files only for the connected user.
## 6. Chat integration
Knowledge search endpoint accepts language en/ta/si and returns matched chunks with source labels. The browser sends the owner admin token only when entered by the owner; it is not persisted in browser storage. Never publish that token or service-role key.
