"""
SQLAlchemy ORM model for the `categories` table.
"""

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.types import TIMESTAMPTZ


class Category(Base):
    """Mercado Livre category node in the hierarchy tree."""

    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    parent_id: Mapped[str | None] = mapped_column(
        Text,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    path_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Self-referential relationships
    children: Mapped[list["Category"]] = relationship(
        "Category",
        back_populates="parent",
        foreign_keys=[parent_id],
    )
    parent: Mapped["Category | None"] = relationship(
        "Category",
        back_populates="children",
        remote_side="Category.id",
        foreign_keys=[parent_id],
    )
