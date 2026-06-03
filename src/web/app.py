"""FastAPI application for the MAGIK Engine web interface."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.storage.json_storage import JSONStorage
from src.storage.types import JsonStore
from src.web.routes import characters, home


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data"
WEB_ROOT = Path(__file__).resolve().parent
TEMPLATES_PATH = WEB_ROOT / "templates"
STATIC_PATH = WEB_ROOT / "static"


def create_app(storage: JsonStore | None = None) -> FastAPI:
    app = FastAPI(title="MAGIK Engine", version="0.9")
    app.state.storage = storage or JSONStorage(DATA_PATH)
    app.state.templates = Jinja2Templates(directory=str(TEMPLATES_PATH))
    app.mount("/static", StaticFiles(directory=str(STATIC_PATH)), name="static")
    app.include_router(home.router)
    app.include_router(characters.router)
    return app


def get_storage_from_app(app: Any) -> JsonStore:
    return app.state.storage


def get_templates_from_app(app: Any) -> Jinja2Templates:
    return app.state.templates


app = create_app()
