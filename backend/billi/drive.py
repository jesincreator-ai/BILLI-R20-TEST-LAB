"""Read-only Google Drive API v3 adapter using a folder-shared service account."""
from __future__ import annotations

import json
from typing import Any


class DriveNotConfigured(RuntimeError):
    pass


class GoogleDriveReader:
    def __init__(self, service_account_json: str | None, folder_id: str | None) -> None:
        self.service_account_json = service_account_json or ""
        self.folder_id = folder_id or ""
        self._service: Any | None = None

    @property
    def configured(self) -> bool:
        return bool(self.service_account_json and self.folder_id)

    def _get_service(self) -> Any:
        if not self.configured:
            raise DriveNotConfigured("GOOGLE_SERVICE_ACCOUNT_JSON and BILLI_DRIVE_FOLDER_ID are required")
        if self._service is None:
            try:
                from google.oauth2.service_account import Credentials
                from googleapiclient.discovery import build
            except ImportError as exc:
                raise RuntimeError("Drive support requires google-auth and google-api-python-client") from exc
            try:
                info = json.loads(self.service_account_json)
            except json.JSONDecodeError as exc:
                raise DriveNotConfigured("GOOGLE_SERVICE_ACCOUNT_JSON must contain valid service-account JSON") from exc
            credentials = Credentials.from_service_account_info(
                info,
                scopes=["https://www.googleapis.com/auth/drive.readonly"],
            )
            self._service = build("drive", "v3", credentials=credentials, cache_discovery=False)
        return self._service

    def list_children(self, folder_id: str, page_token: str | None = None, page_size: int = 100) -> dict[str, Any]:
        service = self._get_service()
        arguments: dict[str, Any] = {
            "q": f"'{folder_id}' in parents and trashed = false",
            "pageSize": max(1, min(page_size, 1000)),
            "orderBy": "name",
            "fields": "nextPageToken,files(id,name,mimeType,modifiedTime,md5Checksum,size,webViewLink,parents,shortcutDetails)",
            "supportsAllDrives": True,
            "includeItemsFromAllDrives": True,
        }
        if page_token:
            arguments["pageToken"] = page_token
        return service.files().list(**arguments).execute()

    def _workspace_export_type(self, mime_type: str) -> str | None:
        if mime_type == "application/vnd.google-apps.document":
            return "text/plain"
        if mime_type == "application/vnd.google-apps.spreadsheet":
            return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if mime_type == "application/vnd.google-apps.presentation":
            return "application/pdf"
        return None

    def download(self, metadata: dict[str, Any]) -> tuple[bytes, str]:
        service = self._get_service()
        file_id = metadata["id"]
        mime_type = metadata.get("mimeType", "application/octet-stream")
        export_type = self._workspace_export_type(mime_type)
        if export_type:
            data = service.files().export(fileId=file_id, mimeType=export_type).execute()
            return data, export_type
        if mime_type == "application/vnd.google-apps.folder":
            raise ValueError("Folders cannot be downloaded")
        if mime_type == "application/vnd.google-apps.shortcut":
            raise ValueError("Drive shortcuts are not indexed; scan the original item from its folder")
        data = service.files().get(fileId=file_id, alt="media", supportsAllDrives=True).execute()
        if not isinstance(data, bytes):
            data = bytes(data)
        return data, mime_type


def file_version(metadata: dict[str, Any]) -> str:
    checksum = metadata.get("md5Checksum")
    if checksum:
        return str(checksum)
    return ":".join(
        str(metadata.get(field) or "")
        for field in ("modifiedTime", "size", "name", "mimeType")
    )
