"""Deterministic multilingual response composition for BILLI R-20.

This module is intentionally provider-free: it detects the requested language
from explicit input or simple script markers and returns vetted local phrases.
It does not claim machine translation or LLM output.
"""
from __future__ import annotations

SUPPORTED_RESPONSE_LANGUAGES = {"en", "ta", "si"}

def detect_language(text: str) -> str:
    if any("\u0b80" <= ch <= "\u0bff" for ch in text):
        return "ta"
    if any("\u0d80" <= ch <= "\u0dff" for ch in text):
        return "si"
    return "en"

def choose_language(requested: str | None, text: str) -> str:
    if requested:
        value = requested.lower().strip()
        if value not in SUPPORTED_RESPONSE_LANGUAGES:
            raise ValueError(f"unsupported response language: {requested}")
        return value
    return detect_language(text)

RESPONSES = {
    "greeting": {
        "en": "Hello! BILLI R-20 deterministic demo router is online.",
        "ta": "வணக்கம்! BILLI R-20 நிர்ணயிக்கப்பட்ட டெமோ ரூட்டர் இயங்குகிறது.",
        "si": "ආයුබෝවන්! BILLI R-20 නියත ඩෙමෝ රවුටරය ක්‍රියාත්මකයි.",
    },
    "help": {
        "en": "I can route intents, search configured local knowledge, and store memory only with explicit consent.",
        "ta": "நான் நோக்கங்களை வழிமாற்றி, அமைக்கப்பட்ட உள்ளூர் அறிவைத் தேடி, தெளிவான ஒப்புதலுடன் மட்டுமே நினைவகத்தைச் சேமிக்க முடியும்.",
        "si": "මට අරමුණු හඳුනාගෙන, සකස් කළ දේශීය දැනුම සෙවීමටත්, පැහැදිලි අනුමතියක් ඇති විට පමණක් මතකය සුරැකීමටත් හැකිය.",
    },
    "knowledge_search": {
        "en": "Local knowledge retrieval is available when BILLI_KNOWLEDGE_DB is configured.",
        "ta": "BILLI_KNOWLEDGE_DB அமைக்கப்பட்டால் உள்ளூர் அறிவு தேடல் கிடைக்கும்.",
        "si": "BILLI_KNOWLEDGE_DB සකස් කළ විට දේශීය දැනුම සෙවීම ලබා ගත හැක.",
    },
    "status": {
        "en": "API is running. Local knowledge and memory status are reported by /health.",
        "ta": "API இயங்குகிறது. உள்ளூர் அறிவு மற்றும் நினைவக நிலை /health மூலம் தெரிவிக்கப்படுகிறது.",
        "si": "API ක්‍රියාත්මකයි. දේශීය දැනුම සහ මතක තත්ත්වය /health හරහා පෙන්වයි.",
    },
    "unknown": {
        "en": "I received your message. An LLM provider is not configured yet.",
        "ta": "உங்கள் செய்தி பெறப்பட்டது. LLM வழங்குநர் இன்னும் அமைக்கப்படவில்லை.",
        "si": "ඔබගේ පණිවිඩය ලැබුණා. LLM සැපයුම්කරුවෙකු තවම සකස් කර නැහැ.",
    },
}
