"""BILLI R-20 API: deterministic intent routing plus private local knowledge endpoints."""
import json
import os
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request, Response
from pydantic import BaseModel, Field

from .intent import classify
from .knowledge import KnowledgeDocument, KnowledgeStore, SUPPORTED_LANGUAGES

app = FastAPI(
    title="BILLI R-20 API",
    version="0.3.0",
    description="Deterministic router with optional local SQLite/FTS5 knowledge retrieval.",
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    intent: str
    confidence: float
    response: str
    provider: str = "demo-router"
    knowledge: list[dict] = Field(default_factory=list)


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


def owner_ok(auth: str | None) -> bool:
    token = os.getenv("BILLI_ADMIN_TOKEN")
    return bool(token) and auth == "Bearer " + token


def knowledge_db_path() -> str | None:
    value = os.getenv("BILLI_KNOWLEDGE_DB", "").strip()
    return value or None


def open_knowledge_store() -> KnowledgeStore:
    path = knowledge_db_path()
    if not path:
        raise HTTPException(
            status_code=503,
            detail="Local knowledge is not configured. Set BILLI_KNOWLEDGE_DB to a writable SQLite path.",
        )
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return KnowledgeStore(path)


def require_admin(authorization: str | None) -> None:
    if not owner_ok(authorization):
        raise HTTPException(status_code=401, detail="Admin token required for private knowledge operations")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "ai_provider": "not_configured",
        "database": "local_sqlite_fts5_configured" if knowledge_db_path() else "not_configured",
        "drive": "configured" if os.getenv("GOOGLE_CLIENT_ID") else "not_configured",
    }


@app.post("/api/knowledge/search")
def knowledge_search(payload: SearchRequest, authorization: str | None = Header(default=None)):
    require_admin(authorization)
    if payload.language.lower() not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail="language must be one of en, ta, si")
    store = open_knowledge_store()
    try:
        return {
            "query": payload.query,
            "language": payload.language.lower(),
            "results": store.search(payload.query, payload.language, payload.limit),
            "source": "local_sqlite_fts5",
        }
    finally:
        store.close()


@app.post("/api/knowledge/documents")
def knowledge_upsert(payload: KnowledgeDocumentRequest, authorization: str | None = Header(default=None)):
    require_admin(authorization)
    if payload.language.lower() not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail="language must be one of en, ta, si")
    store = open_knowledge_store()
    try:
        store.upsert(
            KnowledgeDocument(
                doc_id=payload.doc_id,
                title=payload.title,
                content=payload.content,
                language=payload.language,
                source=payload.source,
                metadata=payload.metadata,
            )
        )
        return {"status": "stored", "doc_id": payload.doc_id, "source": "local_sqlite_fts5"}
    finally:
        store.close()


@app.get("/api/knowledge/export")
def knowledge_export(authorization: str | None = Header(default=None)):
    require_admin(authorization)
    store = open_knowledge_store()
    try:
        return Response(
            content=store.export_jsonl(),
            media_type="application/x-ndjson; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="billi-knowledge.jsonl"'},
        )
    finally:
        store.close()


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, authorization: str | None = Header(default=None)):
    intent = classify(payload.message)
    hits: list[dict] = []
    if owner_ok(authorization) and knowledge_db_path():
        store = open_knowledge_store()
        try:
            hits = store.search(payload.message, "en", 4)
        finally:
            store.close()
    replies = {
        "greeting": "Hello! BILLI R-20 deterministic demo router is online. Local knowledge retrieval is enabled when configured.",
        "help": "Intent routing and local knowledge retrieval are available when configured.",
        "knowledge_search": "Local knowledge retrieval can be used when BILLI_KNOWLEDGE_DB is configured.",
        "status": "API is running. Local knowledge status is reported by /health.",
        "unknown": "I received your message. Retrieved knowledge can support answers; an LLM provider is not yet configured.",
    }
    return ChatResponse(
        intent=intent.name,
        confidence=intent.confidence,
        response=replies[intent.name],
        provider="demo-router+local-retrieval" if hits else "demo-router",
        knowledge=hits,
    )
