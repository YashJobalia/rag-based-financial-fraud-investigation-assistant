"""Vercel entrypoint: one Python application with the built React assets on the CDN."""
from pathlib import Path

from fastapi.staticfiles import StaticFiles

from backend.app.main import app

frontend = Path(__file__).resolve().parent / "frontend" / "dist"
if frontend.exists():
    app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
