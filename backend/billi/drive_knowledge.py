"""Read-only Google Drive ingestion and Supabase vector knowledge search."""
import base64, hashlib, json, os, re, time
from typing import Any
import httpx
from cryptography.fernet import Fernet
from fastapi import HTTPException
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from supabase import create_client

SCOPES=["https://www.googleapis.com/auth/drive.readonly"]
LANGS={"en","ta","si"}
def env(name): return os.getenv(name,"").strip()
def supa():
    if not env("SUPABASE_URL") or not env("SUPABASE_SERVICE_ROLE_KEY"): raise HTTPException(503,"Supabase server configuration missing")
    return create_client(env("SUPABASE_URL"),env("SUPABASE_SERVICE_ROLE_KEY"))
def cipher():
    key=env("BILLI_TOKEN_ENCRYPTION_KEY")
    if not key: raise HTTPException(503,"Token encryption key not configured")
    return Fernet(key.encode())
def oauth_flow(state=None):
    cid,secret=env("GOOGLE_CLIENT_ID"),env("GOOGLE_CLIENT_SECRET")
    if not cid or not secret: raise HTTPException(503,"Google OAuth credentials not configured")
    flow=Flow.from_client_config({"web":{"client_id":cid,"client_secret":secret,"auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token"}},scopes=SCOPES,state=state)
    flow.redirect_uri=env("GOOGLE_REDIRECT_URI")
    return flow
def drive_auth_url():
    flow=oauth_flow(); url,state=flow.authorization_url(access_type="offline",include_granted_scopes="true",prompt="consent")
    return url,state
def save_token(token):
    db=supa(); encrypted=cipher().encrypt(json.dumps(token).encode()).decode()
    db.table("billi_drive_oauth_tokens").upsert({"id":"owner","encrypted_token":encrypted}).execute()
def load_creds():
    row=supa().table("billi_drive_oauth_tokens").select("encrypted_token").eq("id","owner").limit(1).execute().data
    if not row: raise HTTPException(401,"Google Drive not connected. Connect Drive first.")
    token=json.loads(cipher().decrypt(row[0]["encrypted_token"].encode()))
    c=Credentials.from_authorized_user_info(token,SCOPES)
    if c.expired and c.refresh_token:
        c.refresh(Request()); save_token(json.loads(c.to_json()))
    return c
def detect_language(text):
    if re.search(r"[\\u0B80-\\u0BFF]",text): return "ta"
    if re.search(r"[\\u0D80-\\u0DFF]",text): return "si"
    return "en"
def chunk_text(text,size=1100,overlap=160):
    clean=re.sub(r"\\s+"," ",text).strip()
    if not clean: return []
    chunks=[]; start=0
    while start<len(clean):
        end=min(start+size,len(clean)); chunks.append(clean[start:end])
        if end==len(clean): break
        start=max(0,end-overlap)
    return chunks
def embed(text):
    key=env("GEMINI_API_KEY")
    if not key: raise HTTPException(503,"GEMINI_API_KEY required for embedding knowledge")
    r=httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={key}",json={"model":"models/text-embedding-004","content":{"parts":[{"text":text[:8000]}]}},timeout=40)
    r.raise_for_status(); return r.json()["embedding"]["values"]
def list_drive_files(creds):
    headers={"Authorization":f"Bearer {creds.token}"}
    files=[]; page=None
    # Full user-visible Drive inventory, read-only; never changes sharing or folder settings.
    q="trashed=false"
    with httpx.Client(timeout=60) as client:
        while True:
            params={"q":q,"pageSize":1000,"orderBy":"modifiedTime desc","fields":"nextPageToken,files(id,name,mimeType,modifiedTime,webViewLink,md5Checksum,size)","supportsAllDrives":"true","includeItemsFromAllDrives":"true"}
            if page: params["pageToken"]=page
            res=client.get("https://www.googleapis.com/drive/v3/files",params=params,headers=headers); res.raise_for_status()
            data=res.json(); files.extend(data.get("files",[])); page=data.get("nextPageToken")
            if not page: break
    return files
def extract_drive_text(file,creds):
    h={"Authorization":f"Bearer {creds.token}"}; mid=file["id"]; mime=file.get("mimeType","")
    with httpx.Client(timeout=120) as c:
        if mime.startswith("application/vnd.google-apps."):
            export="text/plain" if mime in ("application/vnd.google-apps.document","application/vnd.google-apps.presentation") else None
            if mime=="application/vnd.google-apps.spreadsheet": export="text/csv"
            if not export: return ""
            r=c.get(f"https://www.googleapis.com/drive/v3/files/{mid}/export",params={"mimeType":export},headers=h); r.raise_for_status()
            return r.text
        if mime.startswith("text/") or mime in ("application/json","application/xml"):
            r=c.get(f"https://www.googleapis.com/drive/v3/files/{mid}",params={"alt":"media"},headers=h); r.raise_for_status(); return r.text
        if mime=="application/pdf":
            r=c.get(f"https://www.googleapis.com/drive/v3/files/{mid}",params={"alt":"media"},headers=h); r.raise_for_status()
            from pypdf import PdfReader
            import io
            reader=PdfReader(io.BytesIO(r.content)); return "\\n".join(p.extract_text() or "" for p in reader.pages)
        return ""
def ingest_all():
    creds=load_creds(); files=list_drive_files(creds); db=supa(); processed=0; skipped=0
    for f in files:
        mime=f.get("mimeType","")
        if mime in ("application/vnd.google-apps.folder","application/vnd.google-apps.shortcut"): skipped+=1; continue
        try: text=extract_drive_text(f,creds)
        except Exception: skipped+=1; continue
        if not text.strip(): skipped+=1; continue
        checksum=hashlib.sha256(text.encode(errors="ignore")).hexdigest()
        existing=db.table("billi_drive_files").select("checksum").eq("id",f["id"]).limit(1).execute().data
        if existing and existing[0].get("checksum")==checksum: skipped+=1; continue
        lang=detect_language(text)
        meta={"name":f.get("name",""),"mime_type":mime,"modified_time":f.get("modifiedTime"),"web_view_link":f.get("webViewLink"),"private_source":True}
        db.table("billi_drive_files").upsert({"id":f["id"],"name":f.get("name","(unnamed)"),"mime_type":mime,"modified_time":f.get("modifiedTime"),"web_view_link":f.get("webViewLink"),"checksum":checksum,"language":lang,"private_source":True}).execute()
        db.table("billi_knowledge_chunks").delete().eq("drive_file_id",f["id"]).execute()
        for i,part in enumerate(chunk_text(text)):
            vector=embed(part)
            db.table("billi_knowledge_chunks").insert({"drive_file_id":f["id"],"chunk_index":i,"content":part,"language":detect_language(part),"embedding":vector,"metadata":meta}).execute()
        processed+=1
    return {"listed":len(files),"processed":processed,"skipped":skipped,"languages":["en","ta","si"]}
def search_knowledge(query,language="en",limit=6):
    v=embed(query)
    return supa().rpc("billi_match_knowledge",{"query_embedding":v,"match_count":limit,"language_filter":language if language in LANGS else None}).execute().data
