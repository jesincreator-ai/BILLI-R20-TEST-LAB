"""BILLI R-20 FastAPI endpoints for private, grounded knowledge access."""
from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .drive import DriveNotConfigured, GoogleDriveReader
from .drive_sync import DriveSyncNotReady, DriveSyncService
from .embeddings import GeminiProvider
from .rag import BilliRAG, KnowledgeNotConfigured
from .security import token_matches
from .settings import Settings
from .supabase_store import SupabaseNotConfigured, SupabaseRequestError, SupabaseStore

app = FastAPI(
    title="BILLI R-20 API",
    version="0.2.0",
    description="Private multilingual Drive knowledge retrieval for BILLI R-20.",
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    language: str = Field(default="auto", max_length=5)


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    language: str = Field(default="auto", max_length=5)
    limit: int = Field(default=8, ge=1, le=20)


class DriveSyncRequest(BaseModel):
    max_files: int = Field(default=5, ge=1, le=10)


def _settings() -> Settings:
    return Settings.from_env()


def _require_admin(x_billi_admin_token: str | None = Header(default=None)) -> None:
    settings = _settings()
    if not settings.private_access_configured:
        raise HTTPException(status_code=503, detail="Private BILLI access is not configured by the administrator.")
    if not token_matches(x_billi_admin_token, settings.admin_token):
        raise HTTPException(status_code=401, detail="A valid BILLI access token is required.")


def _services() -> tuple[Settings, SupabaseStore, GeminiProvider]:
    settings = _settings()
    store = SupabaseStore(settings.supabase_url, settings.supabase_secret_key)
    gemini = GeminiProvider(
        settings.gemini_api_key or None,
        embedding_model=settings.embedding_model,
        answer_model=settings.answer_model,
        dimensions=settings.embedding_dimensions,
    )
    return settings, store, gemini


@app.get("/health")
def health() -> dict[str, Any]:
    settings = _settings()
    return {
        "status": "ok",
        "database": "configured" if settings.supabase_configured else "not_configured",
        "drive": "configured" if settings.drive_configured else "not_configured",
        "gemini": "configured" if settings.gemini_configured else "not_configured",
        "private_access": "configured" if settings.private_access_configured else "not_configured",
        "supported_languages": ["en", "ta", "si"],
    }


@app.get("/api/integrations/status", dependencies=[Depends(_require_admin)])
def integration_status() -> dict[str, Any]:
    settings, store, _ = _services()
    database_reachable = False
    database_error = None
    if store.configured:
        try:
            database_reachable = store.ping()
        except SupabaseRequestError as exc:
            database_error = str(exc)[:250]
    return {
        "supabase": {
            "configured": settings.supabase_configured,
            "reachable": database_reachable,
            "error": database_error,
        },
        "google_drive": {"configured": settings.drive_configured, "scope": "read-only, configured folder"},
        "gemini": {
            "configured": settings.gemini_configured,
            "embedding_model": settings.embedding_model,
            "answer_model": settings.answer_model,
            "dimensions": settings.embedding_dimensions,
        },
        "languages": ["en", "ta", "si"],
    }


@app.get("/api/knowledge/stats", dependencies=[Depends(_require_admin)])
def knowledge_stats() -> dict[str, Any]:
    _, store, _ = _services()
    try:
        return store.knowledge_stats()
    except SupabaseNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except SupabaseRequestError as exc:
        raise HTTPException(status_code=502, detail="Supabase could not return knowledge statistics.") from exc


@app.post("/api/knowledge/search", dependencies=[Depends(_require_admin)])
def knowledge_search(payload: KnowledgeSearchRequest) -> dict[str, Any]:
    _, store, gemini = _services()
    try:
        results = BilliRAG(store, gemini).search(payload.query, payload.language, payload.limit)
        return {"query": payload.query, "results": results, "count": len(results)}
    except KnowledgeNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (SupabaseNotConfigured, SupabaseRequestError, RuntimeError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)[:300]) from exc


@app.post("/api/chat", dependencies=[Depends(_require_admin)])
def chat(payload: ChatRequest) -> dict[str, Any]:
    _, store, gemini = _services()
    try:
        result = BilliRAG(store, gemini).chat(payload.message, payload.language)
        return {
            "intent": "knowledge_answer" if result["sources"] else "knowledge_not_found",
            "confidence": 0.85 if result["sources"] else 0.0,
            **result,
        }
    except KnowledgeNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (SupabaseNotConfigured, SupabaseRequestError, RuntimeError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)[:300]) from exc


@app.post("/api/drive/sync", dependencies=[Depends(_require_admin)])
def start_drive_sync(payload: DriveSyncRequest) -> dict[str, Any]:
    settings, store, gemini = _services()
    drive = GoogleDriveReader(settings.google_service_account_json, settings.drive_folder_id)
    service = DriveSyncService(store, drive, gemini, settings.max_file_bytes, settings.drive_page_size)
    try:
        job = service.start(settings.drive_folder_id)
        return service.step(job["id"], payload.max_files)
    except DriveSyncNotReady as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (SupabaseNotConfigured, SupabaseRequestError, DriveNotConfigured, RuntimeError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)[:300]) from exc


@app.post("/api/drive/sync/{job_id}/step", dependencies=[Depends(_require_admin)])
def continue_drive_sync(job_id: str, payload: DriveSyncRequest) -> dict[str, Any]:
    settings, store, gemini = _services()
    drive = GoogleDriveReader(settings.google_service_account_json, settings.drive_folder_id)
    service = DriveSyncService(store, drive, gemini, settings.max_file_bytes, settings.drive_page_size)
    try:
        return service.step(job_id, payload.max_files)
    except DriveSyncNotReady as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (SupabaseNotConfigured, SupabaseRequestError, DriveNotConfigured, RuntimeError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)[:300]) from exc


@app.get("/api/drive/sync/{job_id}", dependencies=[Depends(_require_admin)])
def get_drive_sync(job_id: str) -> dict[str, Any]:
    _, store, _ = _services()
    try:
        job = store.get_sync_job(job_id)
    except (SupabaseNotConfigured, SupabaseRequestError) as exc:
        raise HTTPException(status_code=502, detail="Could not read the Drive sync job.") from exc
    if not job:
        raise HTTPException(status_code=404, detail="Drive sync job was not found.")
    return job
