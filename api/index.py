"""Vercel entrypoint for the BILLI R-20 FastAPI application.
Keeps deployment at the repository root while reusing the backend package.
"""
from backend.billi.api import app

__all__ = ["app"]
