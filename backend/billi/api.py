"""BILLI R-20 API: deterministic intent routing plus private knowledge endpoints."""
import os, json
from fastapi import FastAPI, Header, HTTPException, Response, Request
from pydantic import BaseModel, Field
from .intent import classify
app=FastAPI(title="BILLI R-20 API",version="0.2.1",description="Demo router with private Drive/Supabase knowledge search.")
class ChatRequest(BaseModel):
 message:str=Field(min_length=1,max_length=4000)
class SearchRequest(BaseModel):
 query:str=Field(min_length=1,max_length=1000)
 language:str="en"
 limit:int=Field(default=6,ge=1,le=20)
def owner_ok(auth):
 return bool(os.getenv("BILLI_ADMIN_TOKEN")) and auth=="Bearer "+os.getenv("BILLI_ADMIN_TOKEN")
@app.get("/health")
def health():
 return {"status":"ok","ai_provider":"not_configured","database":"supabase" if os.getenv("SUPABASE_URL") else "not_configured","drive":"configured" if os.getenv("GOOGLE_CLIENT_ID") else "not_configured"}
@app.get("/api/drive/status")
def drive_status():
 try:
  from .drive_knowledge import supa
  connected=bool(supa().table("billi_drive_oauth_tokens").select("id").eq("id","owner").limit(1).execute().data)
 except Exception: connected=False
 return {"connected":connected,"supabase_configured":bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY")),"oauth_configured":bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET")),"embedding_configured":bool(os.getenv("GEMINI_API_KEY")),"languages":["en","ta","si"],"privacy":"Drive read-only; source sharing unchanged"}
@app.get("/api/drive/oauth/start")
def drive_oauth_start(response:Response):
 from .drive_knowledge import drive_auth_url
 url,state=drive_auth_url()
 response.set_cookie("billi_oauth_state",state,httponly=True,secure=True,samesite="lax",max_age=600)
 return {"authorization_url":url}
@app.get("/api/drive/oauth/callback")
def drive_oauth_callback(code:str,state:str,request:Request):
 if not state or state!=request.cookies.get("billi_oauth_state"): raise HTTPException(400,"OAuth state validation failed")
 from .drive_knowledge import oauth_flow,save_token
 flow=oauth_flow(state=state);flow.fetch_token(code=code);save_token(json.loads(flow.credentials.to_json()))
 from fastapi.responses import RedirectResponse
 response=RedirectResponse(url="/?drive=connected",status_code=303);response.delete_cookie("billi_oauth_state");return response
@app.post("/api/drive/sync")
def drive_sync(authorization:str|None=Header(default=None)):
 if not owner_ok(authorization): raise HTTPException(401,"Admin token required for full Drive sync")
 from .drive_knowledge import ingest_all
 return ingest_all()
@app.post("/api/knowledge/search")
def knowledge_search(payload:SearchRequest,authorization:str|None=Header(default=None)):
 if not owner_ok(authorization): raise HTTPException(401,"Admin token required for private knowledge search")
 from .drive_knowledge import search_knowledge
 return {"query":payload.query,"language":payload.language,"results":search_knowledge(payload.query,payload.language,payload.limit)}
@app.post("/api/chat",response_model=None)
def chat(payload:ChatRequest,authorization:str|None=Header(default=None)):
 intent=classify(payload.message);hits=[]
 if owner_ok(authorization):
  try:
   from .drive_knowledge import search_knowledge
   hits=search_knowledge(payload.message,"en",4)
  except Exception: hits=[]
 replies={"greeting":"Hello! BILLI R-20 API is online. Knowledge retrieval is enabled when configured.","help":"Intent routing and knowledge retrieval are available when configured.","knowledge_search":"Knowledge retrieval can be used when Supabase and Gemini are configured.","status":"API is running. Drive/Supabase status is available at /api/drive/status.","unknown":"I received your message. Retrieved knowledge can support answers; an LLM provider is not yet configured."}
 return {"intent":intent.name,"confidence":intent.confidence,"response":replies[intent.name],"provider":"demo-router+retrieval" if hits else "demo-router","knowledge":hits}
