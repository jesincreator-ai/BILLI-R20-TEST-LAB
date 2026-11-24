"""Resumable, recursive Drive-folder indexing into Supabase."""
from __future__ import annotations

from datetime import datetime, timezone
import uuid
from typing import Any

from .chunking import chunk_text
from .drive import file_version
from .embeddings import GeminiProvider
from .extractors import UnsupportedFileType, extract_text
from .language import detect_language
from .supabase_store import SupabaseStore


FOLDER_MIME = "application/vnd.google-apps.folder"


class DriveSyncNotReady(RuntimeError):
    pass


def needs_reindex(existing: dict[str, Any] | None, metadata: dict[str, Any]) -> bool:
    if not existing:
        return True
    return existing.get("version_key") != file_version(metadata) or existing.get("status") != "indexed"


class DriveSyncService:
    def __init__(
        self,
        store: SupabaseStore,
        drive: Any,
        gemini: GeminiProvider,
        max_file_bytes: int = 10 * 1024 * 1024,
        page_size: int = 100,
    ) -> None:
        self.store = store
        self.drive = drive
        self.gemini = gemini
        self.max_file_bytes = max_file_bytes
        self.page_size = page_size

    def start(self, folder_id: str) -> dict[str, Any]:
        if not folder_id:
            raise DriveSyncNotReady("BILLI_DRIVE_FOLDER_ID is not configured")
        if not self.store.configured:
            raise DriveSyncNotReady("Supabase is not configured")
        if not getattr(self.drive, "configured", True):
            raise DriveSyncNotReady("Google Drive service-account access is not configured")
        job_id = str(uuid.uuid4())
        job = {
            "id": job_id,
            "folder_id": folder_id,
            "status": "running",
            "state": {
                "folder_queue": [folder_id],
                "active_folder_id": None,
                "next_page_token": None,
                "pending_files": [],
            },
            "files_seen": 0,
            "files_indexed": 0,
            "files_skipped": 0,
            "error": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.store.create_sync_job(job)

    def _index_one(self, metadata: dict[str, Any]) -> str:
        file_id = metadata["id"]
        version = file_version(metadata)
        existing = self.store.get_drive_file(file_id)
        if not needs_reindex(existing, metadata):
            return "unchanged"

        base = {
            "drive_file_id": file_id,
            "name": metadata.get("name") or file_id,
            "mime_type": metadata.get("mimeType") or "application/octet-stream",
            "modified_time": metadata.get("modifiedTime"),
            "version_key": version,
            "web_view_link": metadata.get("webViewLink"),
            "status": "indexed",
            "last_error": None,
        }
        try:
            payload, content_type = self.drive.download(metadata)
            if len(payload) > self.max_file_bytes:
                raise UnsupportedFileType(f"File exceeds the {self.max_file_bytes // (1024 * 1024)} MB indexing limit")
            text = extract_text(payload, content_type, metadata.get("name", ""))
            if not text:
                raise UnsupportedFileType("No extractable text was found")
            language = detect_language(text)
            chunks = chunk_text(text)
            chunk_rows = []
            for index, chunk in enumerate(chunks):
                embedding = self.gemini.embed_document(base["name"], chunk) if self.gemini.configured else None
                chunk_rows.append(
                    {
                        "chunk_index": index,
                        "language": language,
                        "content": chunk,
                        "embedding": embedding,
                        "metadata": {
                            "source_name": base["name"],
                            "source_mime_type": base["mime_type"],
                            "drive_file_id": file_id,
                        },
                    }
                )
            base["language"] = language
            base["chunk_count"] = len(chunk_rows)
            base["indexed_at"] = datetime.now(timezone.utc).isoformat()
            self.store.replace_file(base, chunk_rows)
            return "indexed"
        except UnsupportedFileType as exc:
            base.update(
                {
                    "status": "skipped",
                    "language": detect_language(metadata.get("name", "")),
                    "chunk_count": 0,
                    "indexed_at": datetime.now(timezone.utc).isoformat(),
                    "last_error": str(exc)[:500],
                }
            )
            self.store.replace_file(base, [])
            return "skipped"

    def step(self, job_id: str, max_files: int = 5) -> dict[str, Any]:
        job = self.store.get_sync_job(job_id)
        if not job:
            raise DriveSyncNotReady("Sync job was not found")
        if job.get("status") in {"completed", "failed"}:
            return job
        state = dict(job.get("state") or {})
        folder_queue = list(state.get("folder_queue") or [])
        pending_files = list(state.get("pending_files") or [])
        active_folder = state.get("active_folder_id")
        next_page_token = state.get("next_page_token")
        seen = int(job.get("files_seen") or 0)
        indexed = int(job.get("files_indexed") or 0)
        skipped = int(job.get("files_skipped") or 0)
        processed_this_step = 0
        loops = 0

        try:
            while processed_this_step < max(1, min(max_files, 10)) and loops < 1000:
                loops += 1
                if pending_files:
                    metadata = pending_files.pop(0)
                    mime_type = metadata.get("mimeType")
                    if mime_type == FOLDER_MIME:
                        folder_queue.append(metadata["id"])
                        continue
                    if mime_type == "application/vnd.google-apps.shortcut":
                        seen += 1
                        skipped += 1
                        processed_this_step += 1
                        continue
                    seen += 1
                    outcome = self._index_one(metadata)
                    if outcome in {"indexed", "unchanged"}:
                        indexed += 1
                    else:
                        skipped += 1
                    processed_this_step += 1
                    continue

                if active_folder and next_page_token:
                    page = self.drive.list_children(active_folder, next_page_token, self.page_size)
                    pending_files.extend(page.get("files") or [])
                    next_page_token = page.get("nextPageToken")
                    if not next_page_token:
                        active_folder = None
                    continue

                if active_folder:
                    active_folder = None
                    next_page_token = None
                    continue

                if folder_queue:
                    active_folder = folder_queue.pop(0)
                    page = self.drive.list_children(active_folder, None, self.page_size)
                    pending_files.extend(page.get("files") or [])
                    next_page_token = page.get("nextPageToken")
                    if not pending_files and not next_page_token:
                        active_folder = None
                    continue

                break

            done = not pending_files and not folder_queue and not active_folder
            updated = {
                "state": {
                    "folder_queue": folder_queue,
                    "active_folder_id": active_folder,
                    "next_page_token": next_page_token,
                    "pending_files": pending_files,
                },
                "files_seen": seen,
                "files_indexed": indexed,
                "files_skipped": skipped,
                "status": "completed" if done else "running",
                "error": None,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            return self.store.update_sync_job(job_id, updated) or {**job, **updated}
        except Exception as exc:
            updated = {
                "status": "failed",
                "error": str(exc)[:800],
                "state": {
                    "folder_queue": folder_queue,
                    "active_folder_id": active_folder,
                    "next_page_token": next_page_token,
                    "pending_files": pending_files,
                },
                "files_seen": seen,
                "files_indexed": indexed,
                "files_skipped": skipped,
            }
            self.store.update_sync_job(job_id, updated)
            raise
