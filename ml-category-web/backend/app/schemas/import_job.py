"""Pydantic schemas for import job endpoints."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ImportStartResponse(BaseModel):
    job_id: str
    status: str = "pending"


class ImportStatusOut(BaseModel):
    job_id: str
    status: Literal["pending", "running", "completed", "failed"]
    processed: int
    total_estimated: int
    started_at: datetime | None
    finished_at: datetime | None
    error_count: int


class SSEProgressEvent(BaseModel):
    processed: int
    total_estimated: int
    percent: float
    current_category: str
    status: str
