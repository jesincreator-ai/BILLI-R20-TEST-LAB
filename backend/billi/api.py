"""BILLI R-20 API: deterministic intent routing plus private local knowledge and consent-gated memory endpoints."""
import os
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Response
from pydantic import BaseModel, Field

from .intent import classify
from .knowledge import KnowledgeDocument, KnowledgeStore, SUPPORTED_LANGUAGES
from .memory import MemoryStore
from .language import RESPONSES, choose_language

app = FastAPI(
    title="BILLI R-20 API",
    version="0.4.0",
    description="Deterministic router with optional local SQLite/FTS5 knowledge and consent-gated memory.",
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    remember_key: str | None = Field(default=None, min_length=1, max_length=200)
    remember_value: str | None = Field(default=None, min_length=1, max_length=4000)
    memory_consent: bool = False
    response_language: str | None = Field(default=None)


class ChatResponse(BaseModel):
    intent: str
    confidence: float
    response: str
    provider: str = "demo-router"
    knowledge: list[dict] = Field(default_factory=list)
    memory: dict = Field(default_factory=dict)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    language: str = "en"
    limit: int = Field(default=6, ge=1, le=20)


class KnowledgeDocumentRequest(BaseModel):
    doc_id: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1, max_length=100_000)
    language: str = "en"
    source: str = Field(default="api", min_length=1, max_length=200)
    metadata: dict[str, object] = Field(default_factory=dict)


class MemoryRememberRequest(BaseModel):
    key: str = Field(min_length=1, max_length=200)
    value: str = Field(min_length=1, max_length=4000)
    consent: bool = False


class MemoryRecallRequest(BaseModel):
    key: str = Field(min_length=1, max_length=200)
    consent: bool = False


def owner_ok(auth: str | None) -> bool:
    token = os.getenv("BILLI_ADMIN_TOKEN")
    return bool(token) and auth == "Bearer " + token


def knowledge_db_path() -> str | None:
    value = os.getenv("BILLI_KNOWLEDGE_DB", "").strip()
    return value or None


def memory_db_path() -> str | None:
    value = os.getenv("BILLI_MEMORY_DB", "").strip()
    return value or None


def open_knowledge_store() -> KnowledgeStore:
    path = knowledge_db_path()
    if not path:
        raise HTTPException(status_code=503, detail="Local knowledge is not configured. Set BILLI_KNOWLEDGE_DB.")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return KnowledgeStore(path)


def open_memory_store() -> MemoryStore:
    path = memory_db_path()
    if not path:
        raise HTTPException(status_code=503, detail="Local memory is not configured. Set BILLI_MEMORY_DB.")
    return MemoryStore(path)


def require_admin(authorization: str | None) -> None:
    if not owner_ok(authorization):
        raise HTTPException(status_code=401, detail="Admin token required for private operations")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "ai_provider": "not_configured",
        "database": "local_sqlite_fts5_configured" if knowledge_db_path() else "not_configured",
        "memory": "local_sqlite_consent_gated_configured" if memory_db_path() else "not_configured",
        "drive": "configured" if os.getenv("GOOGLE_CLIENT_ID") else "not_configured",
    }


@app.post("/api/knowledge/search")
def knowledge_search(payload: SearchRequest, authorization: str | None = Header(default=None)):
    require_admin(authorization)
    if payload.language.lower() not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail="language must be one of en, ta, si")
    store = open_knowledge_store()
    try:
        return {"query": payload.query, "language": payload.language.lower(), "results": store.search(payload.query, payload.language, payload.limit), "source": "local_sqlite_fts5"}
    finally:
        store.close()


@app.post("/api/knowledge/documents")
def knowledge_upsert(payload: KnowledgeDocumentRequest, authorization: str | None = Header(default=None)):
    require_admin(authorization)
    if payload.language.lower() not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail="language must be one of en, ta, si")
    store = open_knowledge_store()
    try:
        store.upsert(KnowledgeDocument(doc_id=payload.doc_id, title=payload.title, content=payload.content, language=payload.language, source=payload.source, metadata=payload.metadata))
        return {"status": "stored", "doc_id": payload.doc_id, "source": "local_sqlite_fts5"}
    finally:
        store.close()


@app.get("/api/knowledge/export")
def knowledge_export(authorization: str | None = Header(default=None)):
    require_admin(authorization)
    store = open_knowledge_store()
    try:
        return Response(content=store.export_jsonl(), media_type="application/x-ndjson; charset=utf-8", headers={"Content-Disposition": 'attachment; filename="billi-knowledge.jsonl"'})
    finally:
        store.close()


@app.post("/api/memory/remember")
def memory_remember(payload: MemoryRememberRequest, authorization: str | None = Header(default=None)):
    require_admin(authorization)
    if not payload.consent:
        return {"status": "not_stored", "reason": "explicit_consent_required"}
    store = open_memory_store()
    try:
        stored = store.remember(payload.key, payload.value, consent=True)
        return {"status": "stored" if stored else "not_stored", "key": payload.key, "source": "local_sqlite_consent_gated"}
    finally:
        store.close()


@app.post("/api/memory/recall")
def memory_recall(payload: MemoryRecallRequest, authorization: str | None = Header(default=None)):
    require_admin(authorization)
    if not payload.consent:
        return {"status": "not_returned", "reason": "explicit_consent_required", "value": None}
    store = open_memory_store()
    try:
        return {"status": "ok", "key": payload.key, "value": store.recall(payload.key, consent=True), "source": "local_sqlite_consent_gated"}
    finally:
        store.close()


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, authorization: str | None = Header(default=None)):
    intent = classify(payload.message)
    hits: list[dict] = []
    memory_result = {"status": "not_requested"}
    if owner_ok(authorization) and knowledge_db_path():
        store = open_knowledge_store()
        try:
            hits = store.search(payload.message, "en", 4)
        finally:
            store.close()
    if payload.remember_key and payload.remember_value:
        if not payload.memory_consent:
            memory_result = {"status": "not_stored", "reason": "explicit_consent_required"}
        elif owner_ok(authorization) and memory_db_path():
            store = open_memory_store()
            try:
                memory_result = {"status": "stored" if store.remember(payload.remember_key, payload.remember_value, consent=True) else "not_stored", "key": payload.remember_key}
            finally:
                store.close()
        else:
            memory_result = {"status": "not_stored", "reason": "admin_and_memory_configuration_required"}
    try:
        response_language = choose_language(payload.response_language, payload.message)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response_text = RESPONSES[intent.name][response_language]
    return ChatResponse(intent=intent.name, confidence=intent.confidence, response=response_text, provider="demo-router+local-retrieval" if hits else "demo-router", knowledge=hits, memory=memory_result)
