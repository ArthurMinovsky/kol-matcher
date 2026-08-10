"""Shared pytest configuration for project-root test runs."""
from __future__ import annotations

import sys
from pathlib import Path

_API_PATH = Path(__file__).parent.parent / "apps" / "api"
if str(_API_PATH) not in sys.path:
    sys.path.insert(0, str(_API_PATH))
