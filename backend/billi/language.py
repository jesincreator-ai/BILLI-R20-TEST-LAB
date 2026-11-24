"""Lightweight Unicode-script language detection for English, Tamil and Sinhala."""
from __future__ import annotations

SUPPORTED_LANGUAGES = {"en", "ta", "si"}


def detect_language(text: str) -> str:
    counts = {"ta": 0, "si": 0, "en": 0}
    for char in text or "":
        code = ord(char)
        if 0x0B80 <= code <= 0x0BFF:
            counts["ta"] += 1
        elif 0x0D80 <= code <= 0x0DFF:
            counts["si"] += 1
        elif char.isalpha():
            counts["en"] += 1
    if counts["ta"] or counts["si"]:
        return "ta" if counts["ta"] >= counts["si"] else "si"
    return "en"


def normalize_language(language: str | None, text: str = "") -> str:
    candidate = (language or "auto").strip().lower()
    if candidate == "auto":
        return detect_language(text)
    return candidate if candidate in SUPPORTED_LANGUAGES else detect_language(text)
