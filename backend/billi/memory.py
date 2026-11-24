"""Simple local consent gate. Memory is disabled until explicitly opted in."""
from pathlib import Path
import sqlite3

class MemoryStore:
    def __init__(self, db_path: str | Path = "data/billi.sqlite3"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS memory (id INTEGER PRIMARY KEY, key TEXT UNIQUE NOT NULL, value TEXT NOT NULL)")

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def remember(self, key: str, value: str, consent: bool = False) -> bool:
        if not consent:
            return False
        with self._connect() as conn:
            conn.execute("INSERT INTO memory(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
        return True

    def recall(self, key: str, consent: bool = False) -> str | None:
        if not consent:
            return None
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM memory WHERE key=?", (key,)).fetchone()
        return row[0] if row else None
