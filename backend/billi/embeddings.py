"""Gemini embeddings and answer generation. Clients are created lazily."""
from __future__ import annotations

from typing import Any


class GeminiNotConfigured(RuntimeError):
    pass


class GeminiProvider:
    def __init__(
        self,
        api_key: str | None,
        embedding_model: str = "gemini-embedding-2",
        answer_model: str = "gemini-3.8-flash",
        dimensions: int = 768,
        client: Any | None = None,
    ) -> None:
        self.api_key = api_key
        self.embedding_model = embedding_model
        self.answer_model = answer_model
        self.dimensions = dimensions
        self._client = client

    @property
    def configured(self) -> bool:
        return bool(self.api_key or self._client)

    def _get_client(self) -> Any:
        if not self.configured:
            raise GeminiNotConfigured("GEMINI_API_KEY is not configured")
        if self._client is None:
            try:
                from google import genai
            except ImportError as exc:
                raise RuntimeError("Google GenAI SDK is required; install google-genai") from exc
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def _embed(self, text: str) -> list[float]:
        try:
            from google.genai import types
            config = types.EmbedContentConfig(output_dimensionality=self.dimensions)
        except ImportError as exc:
            raise RuntimeError("Google GenAI SDK is required; install google-genai") from exc
        result = self._get_client().models.embed_content(
            model=self.embedding_model,
            contents=text,
            config=config,
        )
        if not result.embeddings:
            raise RuntimeError("Gemini returned no embedding")
        values = [float(value) for value in result.embeddings[0].values]
        if len(values) != self.dimensions:
            raise RuntimeError(f"Expected {self.dimensions} embedding values, received {len(values)}")
        return values

    def embed_document(self, title: str, content: str) -> list[float]:
        prepared = f"title: {title or 'none'} | text: {content}"
        return self._embed(prepared)

    def embed_query(self, query: str) -> list[float]:
        prepared = f"task: search result | query: {query}"
        return self._embed(prepared)

    def answer(self, question: str, language: str, sources: list[dict[str, Any]]) -> str:
        if not sources:
            return "I couldn't find relevant evidence in the connected BILLI knowledge base."
        formatted = []
        for index, source in enumerate(sources, start=1):
            formatted.append(
                f"[{index}] {source.get('source_name', 'Drive document')} "
                f"(language={source.get('language', 'en')}):\n{source.get('content', '')}"
            )
        language_names = {"en": "English", "ta": "Tamil", "si": "Sinhala"}
        prompt = (
            "You are BILLI R-20. Answer only from the supplied knowledge excerpts. "
            "If the excerpts do not contain enough evidence, say so clearly and do not guess. "
            "Cite factual claims with bracket citations such as [1] or [2]. "
            f"Reply in {language_names.get(language, 'English')}.\n\n"
            f"Question: {question}\n\nEvidence:\n" + "\n\n".join(formatted)
        )
        result = self._get_client().models.generate_content(
            model=self.answer_model,
            contents=prompt,
        )
        answer = getattr(result, "text", None)
        if not answer:
            raise RuntimeError("Gemini returned an empty answer")
        return str(answer).strip()
