"""
FastAPI Config Management with Pydantic v2.

Pattern: Read JSON on startup, create defaults if missing, merge on POST.
Config lives in data/settings.json and survives restarts.

Usage:
    from app.core.config import get_settings, update_settings
    
    # Read
    settings = get_settings()
    
    # Update (partial merge)
    updated = update_settings({"language": "vi"})
"""

import json
from pathlib import Path
from pydantic import BaseModel

# Resolve data/ relative to this file's parent (backend/)
_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_SETTINGS_FILE = _DATA_DIR / "settings.json"

# Default settings — define schema here
DEFAULTS = {
    "app_name": "Goha MMO Clone",
    "version": "1.0",
    "theme": "dark",
    "language": "vi",
}


class AppSettings(BaseModel):
    """Pydantic v2 model for app settings. Add fields as needed."""
    app_name: str = "App"
    version: str = "1.0"
    theme: str = "dark"
    language: str = "vi"


def _ensure_data_dir():
    """Create data/ directory if it doesn't exist."""
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read_raw() -> dict:
    """Read settings.json, return defaults if missing or corrupt."""
    _ensure_data_dir()
    if not _SETTINGS_FILE.exists():
        return DEFAULTS.copy()
    try:
        with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return DEFAULTS.copy()


def _write_raw(data: dict):
    """Write settings to disk."""
    _ensure_data_dir()
    with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_settings() -> dict:
    """Return current settings as dict."""
    return _read_raw()


def update_settings(partial: dict) -> dict:
    """
    Merge partial update into settings and persist.
    Only fields present in `partial` are changed; others are preserved.
    Returns the full updated settings dict.
    """
    current = _read_raw()
    current.update(partial)
    _write_raw(current)
    return current


# Router integration example:
#
# from fastapi import APIRouter
# from app.core.config import get_settings, update_settings
#
# router = APIRouter()
#
# @router.get("/settings")
# async def read_settings():
#     return get_settings()
#
# @router.post("/settings")
# async def write_settings(body: dict):
#     return update_settings(body)
