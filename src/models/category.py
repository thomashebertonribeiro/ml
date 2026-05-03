from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CategoryDTO:
    """Data Transfer Object representing a Mercado Livre category."""

    id: str
    name: str
    parent_id: str | None
    level: int
    total_items_in_this_category: int = 0
    path_from_root: list[dict] = field(default_factory=list)
    # [{"id": "MLB1051", "name": "Celulares e Telefones"}, ...]
    children_ids: list[str] = field(default_factory=list)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Serialize the DTO to a JSON-compatible dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id,
            "level": self.level,
            "total_items_in_this_category": self.total_items_in_this_category,
            "path_from_root": self.path_from_root,
            "children_ids": self.children_ids,
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class CategoryDetailDTO(CategoryDTO):
    """Enriched version returned by GET /categories/{id}."""

    picture: str | None = None
    permalink: str | None = None
    settings: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize the DTO to a JSON-compatible dictionary, including detail fields."""
        base = super().to_dict()
        base.update(
            {
                "picture": self.picture,
                "permalink": self.permalink,
                "settings": self.settings,
            }
        )
        return base
