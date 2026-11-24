"""Nanobot Lite: small deterministic intent router (no external model)."""
from dataclasses import dataclass
from typing import Literal

IntentName = Literal["greeting", "help", "knowledge_search", "status", "unknown"]

@dataclass(frozen=True)
class Intent:
    name: IntentName
    confidence: float


def classify(text: str) -> Intent:
    normalized = text.strip().lower()
    if not normalized:
        return Intent("unknown", 0.0)
    if any(word in normalized for word in ("hello", "hi", "hey", "வணக்கம்", "ආයුබෝවන්")):
        return Intent("greeting", 0.85)
    if any(word in normalized for word in ("help", "what can you do", "உதவி", "උදව්")):
        return Intent("help", 0.85)
    if any(word in normalized for word in ("search", "find", "knowledge", "look up", "தேடு", "සොයන්න")):
        return Intent("knowledge_search", 0.75)
    if any(word in normalized for word in ("status", "health", "system", "நிலை", "තත්ත්වය")):
        return Intent("status", 0.75)
    return Intent("unknown", 0.35)
