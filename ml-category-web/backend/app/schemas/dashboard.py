"""Pydantic schemas for dashboard endpoints."""

from datetime import datetime

from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_categories: int
    total_root_categories: int
    total_leaf_categories: int
    max_depth: int
    last_import_at: datetime | None
    changes_last_30_days: int
    categories_by_level: dict[int, int]
