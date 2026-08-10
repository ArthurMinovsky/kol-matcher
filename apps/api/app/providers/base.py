"""Base provider types."""
from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel

from ..models.brand import SourceState

T = TypeVar("T")


class SourceResult(BaseModel, Generic[T]):
    status: SourceState
    data: T | None = None
    captured_at: datetime | None = None
    provider: str
    error: str | None = None
