"""Pydantic schemas for category endpoints."""

from pydantic import BaseModel, ConfigDict


class PathNode(BaseModel):
    id: str
    name: str


class CategoryOut(BaseModel):
    id: str
    name: str
    parent_id: str | None
    level: int
    total_items: int
    path_from_root: list[PathNode]

    model_config = ConfigDict(from_attributes=True)


class CategoryDetail(CategoryOut):
    children: list[CategoryOut] = []


class SearchResponse(BaseModel):
    items: list[CategoryOut]
    total: int
    page: int
    page_size: int
