"""
SQLAlchemy ORM model for the `change_log` table.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base
from app.models.types import TIMESTAMPTZ


class ChangeLog(Base):
    """Records category additions and removals detected during an import job."""

    __tablename__ = "change_log"

    __table_args__ = (
        CheckConstraint(
            "change_type IN ('added', 'removed')",
            name="ck_change_log_change_type",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    change_type: Mapped[str] = mapped_column(Text, nullable=False)
    category_id: Mapped[str] = mapped_column(Text, nullable=False)
    category_name: Mapped[str] = mapped_column(Text, nullable=False)
    parent_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=func.now(), nullable=False
    )
    import_job_id: Mapped[UUID] = mapped_column(
        ForeignKey("import_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
