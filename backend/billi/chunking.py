"""Deterministic character-window chunking with overlap."""
from __future__ import annotations


def chunk_text(text: str, chunk_size: int = 1400, overlap: int = 180) -> list[str]:
    cleaned = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not cleaned:
        return []
    if chunk_size < 1 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("chunk_size must be positive and overlap must be smaller than chunk_size")

    chunks: list[str] = []
    start = 0
    length = len(cleaned)
    while start < length:
        end = min(start + chunk_size, length)
        if end < length:
            boundary = max(cleaned.rfind("\n", start, end), cleaned.rfind(" ", start, end))
            if boundary > start + int(chunk_size * 0.65):
                end = boundary
        piece = cleaned[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= length:
            break
        start = max(start + 1, end - overlap)
    return chunks
