"""Pydantic schemas for scheduler endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class SchedulerStatus(BaseModel):
    active: bool
    last_run_at: datetime | None
    next_run_at: datetime | None
    last_run_result: str | None
    interval_hours: int


class SchedulerConfigUpdate(BaseModel):
    interval_hours: int = Field(ge=1, le=168)
