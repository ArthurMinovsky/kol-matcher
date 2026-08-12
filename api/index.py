"""Vercel serverless entrypoint for the FastAPI application."""
from __future__ import annotations

import sys
from pathlib import Path


API_SOURCE_DIR = Path(__file__).resolve().parents[1] / "apps" / "api"
sys.path.insert(0, str(API_SOURCE_DIR))

from app.main import app
