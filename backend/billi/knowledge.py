"""Small, dependency-free SQLite + FTS5 knowledge store for BILLI R-20.

The store is local-first and intentionally explicit: callers provide the database
path and document content. No files are read implicitly and no hosted persistence
is assumed.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

SUPPORTED_LANGUAGES = {"en", "ta", "si"}


@dataclass(frozen=True)
class KnowledgeDocument:
    doc_id: str
    title: str
    content: str
    language: str = "en"
    source: str = "local"
    metadata: Mapping[str, object] | None = None


class KnowledgeStore:
    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.db_path = str(db_path)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._init_schema()

    def _init_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                language TEXT NOT NULL CHECK(language IN ('en','ta','si')),
                source TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                doc_id UNINDEXED,
                title,
                content,
                language UNINDEXED,
                tokenize='unicode61'
            );
            """
        )
        self.connection.commit()

    def upsert(self, document: KnowledgeDocument) -> None:
        language = document.language.lower()
        if language not in SUPPORTED_LANGUAGES:
            raise ValueError(f"unsupported language: {document.language}")
        metadata_json = json.dumps(document.metadata or {}, ensure_ascii=False, sort_keys=True)
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO documents(doc_id,title,content,language,source,metadata_json)
                VALUES(?,?,?,?,?,?)
                ON CONFLICT(doc_id) DO UPDATE SET
                  title=excluded.title,
                  content=excluded.content,
                  language=excluded.language,
                  source=excluded.source,
                  metadata_json=excluded.metadata_json,
                  updated_at=CURRENT_TIMESTAMP
                """,
                (document.doc_id, document.title, document.content, language, document.source, metadata_json),
            )
            self.connection.execute("DELETE FROM documents_fts WHERE doc_id=?", (document.doc_id,))
            self.connection.execute(
                "INSERT INTO documents_fts(doc_id,title,content,language) VALUES(?,?,?,?)",
                (document.doc_id, document.title, document.content, language),
            )

    def bulk_upsert(self, documents: Iterable[KnowledgeDocument]) -> int:
        count = 0
        for document in documents:
            self.upsert(document)
            count += 1
        return count

    def search(self, query: str, language: str | None = None, limit: int = 6) -> list[dict]:
        if not query.strip():
            return []
        if limit < 1:
            raise ValueError("limit must be positive")
        params: list[object] = [query]
        where = ""
        if language:
            normalized = language.lower()
            if normalized not in SUPPORTED_LANGUAGES:
                raise ValueError(f"unsupported language: {language}")
            where = " AND d.language = ?"
            params.append(normalized)
        params.append(limit)
        rows = self.connection.execute(
            f"""
            SELECT d.doc_id, d.title, d.content, d.language, d.source, d.metadata_json,
                   bm25(documents_fts) AS score
            FROM documents_fts
            JOIN documents d ON d.doc_id = documents_fts.doc_id
            WHERE documents_fts MATCH ? {where}
            ORDER BY score
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [
            {
                "doc_id": row["doc_id"],
                "title": row["title"],
                "snippet": row["content"][:500],
                "language": row["language"],
                "source": row["source"],
                "metadata": json.loads(row["metadata_json"]),
                "score": row["score"],
            }
            for row in rows
        ]

    def export_jsonl(self) -> str:
        rows = self.connection.execute(
            "SELECT doc_id,title,content,language,source,metadata_json FROM documents ORDER BY doc_id"
        ).fetchall()
        return "".join(
            json.dumps(
                {
                    "doc_id": row["doc_id"],
                    "title": row["title"],
                    "content": row["content"],
                    "language": row["language"],
                    "source": row["source"],
                    "metadata": json.loads(row["metadata_json"]),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n"
            for row in rows
        )

    def close(self) -> None:
        self.connection.close()
