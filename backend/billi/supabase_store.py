"""Minimal private Supabase PostgREST repository using the server-side secret key."""
from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen


class SupabaseNotConfigured(RuntimeError):
    pass


class SupabaseRequestError(RuntimeError):
    pass


def vector_literal(values: list[float]) -> str:
    if not values:
        raise ValueError("embedding vector cannot be empty")
    return "[" + ",".join(format(float(value), ".8g") for value in values) + "]"


class SupabaseStore:
    def __init__(self, url: str | None, secret_key: str | None, timeout: int = 20) -> None:
        self.url = (url or "").rstrip("/")
        self.secret_key = secret_key or ""
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        return bool(self.url and self.secret_key)

    def _request(
        self,
        path: str,
        method: str = "GET",
        payload: Any | None = None,
        params: dict[str, str] | None = None,
        prefer: str | None = None,
    ) -> Any:
        if not self.configured:
            raise SupabaseNotConfigured("SUPABASE_URL and SUPABASE_SECRET_KEY are required")
        query = "?" + urlencode(params) if params else ""
        url = f"{self.url}/rest/v1/{path}{query}"
        headers = {
            "apikey": self.secret_key,
            "Authorization": f"Bearer {self.secret_key}",
            "Accept": "application/json",
        }
        data = None
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if prefer:
            headers["Prefer"] = prefer
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read()
                if not body:
                    return None
                try:
                    return json.loads(body.decode("utf-8"))
                except json.JSONDecodeError:
                    return body.decode("utf-8", errors="replace")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise SupabaseRequestError(f"Supabase HTTP {exc.code}: {detail[:800]}") from exc
        except (URLError, TimeoutError) as exc:
            raise SupabaseRequestError(f"Supabase request failed: {exc}") from exc

    def ping(self) -> bool:
        self._request("billi_drive_files", params={"select": "drive_file_id", "limit": "1"})
        return True

    def get_drive_file(self, drive_file_id: str) -> dict[str, Any] | None:
        rows = self._request(
            "billi_drive_files",
            params={
                "drive_file_id": f"eq.{drive_file_id}",
                "select": "*",
                "limit": "1",
            },
        ) or []
        return rows[0] if rows else None

    def replace_file(self, file_row: dict[str, Any], chunks: list[dict[str, Any]]) -> None:
        self._request(
            "rpc/replace_billi_knowledge_file",
            method="POST",
            payload={"p_file": file_row, "p_chunks": chunks},
        )

    def vector_search(self, embedding: list[float], language: str | None, limit: int = 8) -> list[dict[str, Any]]:
        return self._request(
            "rpc/match_billi_knowledge",
            method="POST",
            payload={
                "p_query_embedding": vector_literal(embedding),
                "p_match_count": limit,
                "p_language": language,
            },
        ) or []

    def keyword_search(self, query: str, language: str | None, limit: int = 8) -> list[dict[str, Any]]:
        return self._request(
            "rpc/search_billi_knowledge_keyword",
            method="POST",
            payload={"p_query": query, "p_match_count": limit, "p_language": language},
        ) or []

    def create_sync_job(self, job: dict[str, Any]) -> dict[str, Any]:
        rows = self._request(
            "billi_drive_sync_jobs",
            method="POST",
            payload=job,
            prefer="return=representation",
        )
        return rows[0]

    def get_sync_job(self, job_id: str) -> dict[str, Any] | None:
        rows = self._request(
            "billi_drive_sync_jobs",
            params={"id": f"eq.{job_id}", "select": "*", "limit": "1"},
        ) or []
        return rows[0] if rows else None

    def update_sync_job(self, job_id: str, values: dict[str, Any]) -> dict[str, Any] | None:
        rows = self._request(
            "billi_drive_sync_jobs",
            method="PATCH",
            payload=values,
            params={"id": f"eq.{job_id}"},
            prefer="return=representation",
        ) or []
        return rows[0] if rows else None

    def knowledge_stats(self) -> dict[str, int]:
        sources = self._request("billi_drive_files", params={"select": "drive_file_id", "limit": "1000"}) or []
        chunks = self._request("billi_knowledge_chunks", params={"select": "id", "limit": "1000"}) or []
        return {"sources_sampled": len(sources), "chunks_sampled": len(chunks)}
