"""Language-aware private retrieval and evidence-grounded response composition."""
from __future__ import annotations

from typing import Any

from .embeddings import GeminiProvider
from .language import normalize_language
from .supabase_store import SupabaseStore


class KnowledgeNotConfigured(RuntimeError):
    pass


class BilliRAG:
    def __init__(self, store: SupabaseStore, gemini: GeminiProvider) -> None:
        self.store = store
        self.gemini = gemini

    def search(self, query: str, language: str | None = "auto", limit: int = 8) -> list[dict[str, Any]]:
        if not self.store.configured:
            raise KnowledgeNotConfigured("Supabase knowledge storage is not configured")
        selected_language = normalize_language(language, query)
        if self.gemini.configured:
            embedding = self.gemini.embed_query(query)
            rows = self.store.vector_search(embedding, selected_language, max(1, min(limit, 20)))
        else:
            rows = self.store.keyword_search(query, selected_language, max(1, min(limit, 20)))
        clean = []
        for row in rows:
            clean.append(
                {
                    "content": row.get("content", ""),
                    "source_name": row.get("source_name", "Drive document"),
                    "drive_file_id": row.get("drive_file_id"),
                    "web_view_link": row.get("web_view_link"),
                    "language": row.get("language", selected_language),
                    "similarity": row.get("similarity"),
                }
            )
        return clean

    def chat(self, query: str, language: str | None = "auto") -> dict[str, Any]:
        selected_language = normalize_language(language, query)
        sources = self.search(query, selected_language, limit=6)
        if not sources:
            return {
                "response": "I couldn't find relevant evidence in the connected BILLI knowledge base. Try another wording or check whether the Drive folder has been synced.",
                "provider": "supabase-retrieval",
                "language": selected_language,
                "sources": [],
            }
        if self.gemini.configured:
            response = self.gemini.answer(query, selected_language, sources)
            provider = self.gemini.answer_model
        else:
            excerpts = "\n\n".join(
                f"[{i}] {source['source_name']}: {source['content'][:900]}"
                for i, source in enumerate(sources[:3], start=1)
            )
            response = (
                "Knowledge retrieval is working, but Gemini answer generation is not configured. "
                "Here are the closest indexed passages:\n\n" + excerpts
            )
            provider = "retrieval-only"
        return {
            "response": response,
            "provider": provider,
            "language": selected_language,
            "sources": [
                {
                    "title": source["source_name"],
                    "url": source["web_view_link"],
                    "language": source["language"],
                    "similarity": source["similarity"],
                }
                for source in sources
            ],
        }
