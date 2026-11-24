"""Root Vercel FastAPI entrypoint. Vercel detects the exported `app` object here."""
from backend.billi.api import app

__all__ = ["app"]