"""
app/config.py
Application configuration for the SmartPrep AI backend.

All paths and model settings are centralised here. Services should import
from this module rather than computing paths themselves.
"""

from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Ollama / Model settings
# ---------------------------------------------------------------------------

OLLAMA_BASE_URL: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
CHAT_MODEL: str = os.environ.get("CHAT_MODEL", "llama3.2")
EMBEDDING_MODEL: str = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text")

# ---------------------------------------------------------------------------
# Filesystem paths
# ---------------------------------------------------------------------------

BACKEND_ROOT: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = Path(os.environ.get("DATA_DIR", str(BACKEND_ROOT / "data")))
UPLOADS_DIR: Path = Path(os.environ.get("UPLOADS_DIR", str(DATA_DIR / "uploads")))
CHROMA_DIR: Path = Path(os.environ.get("CHROMA_DIR", str(DATA_DIR / "chroma_store")))
DB_PATH: Path = Path(os.environ.get("DB_PATH", str(DATA_DIR / "metadata.db")))
LOGS_DIR: Path = Path(os.environ.get("LOGS_DIR", str(DATA_DIR / "logs")))
