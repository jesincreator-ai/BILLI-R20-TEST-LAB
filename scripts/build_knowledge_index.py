#!/usr/bin/env python3
"""Build a deterministic, lightweight index from public-safe BILLI knowledge files."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "knowledge" / "public"
OUT = ROOT / "knowledge" / "public" / "index.json"
SUPPORTED = {".md", ".txt", ".json", ".csv"}

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def main() -> None:
    records = []
    if SOURCE.exists():
        for path in sorted(SOURCE.rglob("*")):
            if not path.is_file() or path == OUT or path.suffix.lower() not in SUPPORTED:
                continue
            try:
                raw = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            content = normalize(raw)
            if not content:
                continue
            records.append({
                "id": hashlib.sha256(str(path.relative_to(ROOT)).encode()).hexdigest()[:16],
                "path": str(path.relative_to(ROOT)),
                "language": "und",
                "title": path.stem,
                "content": content,
                "content_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Indexed {len(records)} public-safe knowledge file(s).")

if __name__ == "__main__":
    main()
