"""Environment-backed configuration for the private BILLI knowledge API."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    supabase_url: str = ""
    supabase_secret_key: str = ""
    gemini_api_key: str = ""
    google_service_account_json: str = ""
    drive_folder_id: str = ""
    admin_token: str = ""
    embedding_model: str = "gemini-embedding-2"
    answer_model: str = "gemini-3.8-flash"
    embedding_dimensions: int = 768
    max_file_bytes: int = 10 * 1024 * 1024
    drive_page_size: int = 100

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            supabase_url=os.getenv("SUPABASE_URL", "").strip(),
            supabase_secret_key=(
                os.getenv("SUPABASE_SECRET_KEY", "").strip()
                or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
            ),
            gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
            google_service_account_json=os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip(),
            drive_folder_id=os.getenv("BILLI_DRIVE_FOLDER_ID", "").strip(),
            admin_token=os.getenv("BILLI_ADMIN_TOKEN", ""),
            embedding_model=os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2").strip(),
            answer_model=os.getenv("GEMINI_CHAT_MODEL", "gemini-3.8-flash").strip(),
            embedding_dimensions=int(os.getenv("GEMINI_EMBEDDING_DIMENSIONS", "768")),
            max_file_bytes=max(1, int(os.getenv("BILLI_MAX_DRIVE_FILE_MB", "10"))) * 1024 * 1024,
            drive_page_size=max(1, min(1000, int(os.getenv("BILLI_DRIVE_PAGE_SIZE", "100")))),
        )

    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_secret_key)

    @property
    def drive_configured(self) -> bool:
        return bool(self.google_service_account_json and self.drive_folder_id)

    @property
    def gemini_configured(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def private_access_configured(self) -> bool:
        return bool(self.admin_token)
