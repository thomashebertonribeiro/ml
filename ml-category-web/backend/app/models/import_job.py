"""
SQLAlchemy ORM model for the `import_jobs` table.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base
from app.models.types import TIMESTAMPTZ


class ImportJob(Base):
    """Tracks the lifecycle of a category import operation."""

    __tablename__ = "import_jobs"

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed')",
            name="ck_import_jobs_status",
        ),
        CheckConstraint(
            "triggered_by IN ('manual', 'scheduler')",
            name="ck_import_jobs_triggered_by",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_estimated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ, nullable=True)
    triggered_by: Mapped[str] = mapped_column(Text, nullable=False, default="manual")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=func.now(), nullable=False
    )
