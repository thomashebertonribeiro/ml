"""Pydantic schemas for change log endpoints."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ChangeLogOut(BaseModel):
    id: int
    change_type: Literal["added", "removed"]
    category_id: str
    category_name: str
    parent_id: str | None
    detected_at: datetime
    import_job_id: str


class ChangeSummaryItem(BaseModel):
    month: str  # "2024-01"
    added: int
    removed: int
