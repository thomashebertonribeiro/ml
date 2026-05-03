"""
SQLAlchemy ORM model for the `scheduler_config` table.

This is a singleton table — it always contains exactly one row with id = 1.
"""

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base
from app.models.types import TIMESTAMPTZ


class SchedulerConfig(Base):
    """Singleton configuration for the automatic import scheduler."""

    __tablename__ = "scheduler_config"

    __table_args__ = (
        CheckConstraint("id = 1", name="ck_scheduler_config_singleton"),
        CheckConstraint(
            "interval_hours BETWEEN 1 AND 168",
            name="ck_scheduler_config_interval_hours",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    interval_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ, nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ, nullable=True)
    last_run_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=func.now(), onupdate=func.now(), nullable=False
    )
