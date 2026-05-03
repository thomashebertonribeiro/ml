"""
Scheduler router — requires authentication.

Endpoints:
    GET /scheduler/status  — return current SchedulerStatus
    PUT /scheduler/config  — update interval_hours (1–168 h)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.scheduler_config import SchedulerConfig
from app.models.user import User
from app.schemas.scheduler import SchedulerConfigUpdate, SchedulerStatus
from app.services.exceptions import NotFoundError

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_scheduler_config(db: AsyncSession) -> SchedulerConfig:
    """Fetch the singleton SchedulerConfig row (id = 1).

    Raises:
        NotFoundError (HTTP 404): if the row does not exist (should never
            happen after the initial migration seed).
    """
    result = await db.execute(
        select(SchedulerConfig).where(SchedulerConfig.id == 1)
    )
    config: SchedulerConfig | None = result.scalar_one_or_none()
    if config is None:
        raise NotFoundError("Configuração do scheduler não encontrada.")
    return config


def _config_to_status(config: SchedulerConfig) -> SchedulerStatus:
    """Convert a SchedulerConfig ORM instance to a SchedulerStatus schema."""
    return SchedulerStatus(
        active=config.active,
        last_run_at=config.last_run_at,
        next_run_at=config.next_run_at,
        last_run_result=config.last_run_result,
        interval_hours=config.interval_hours,
    )


# ---------------------------------------------------------------------------
# GET /scheduler/status
# ---------------------------------------------------------------------------


@router.get(
    "/status",
    response_model=SchedulerStatus,
    summary="Get scheduler status",
)
async def get_scheduler_status(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> SchedulerStatus:
    """Return the current scheduler configuration and last-run metadata.

    Reads the singleton row from the ``scheduler_config`` table (id = 1).

    Raises:
        AuthError (HTTP 401): if the request is not authenticated.
        NotFoundError (HTTP 404): if the scheduler config row is missing.
    """
    config = await _get_scheduler_config(db)
    return _config_to_status(config)


# ---------------------------------------------------------------------------
# PUT /scheduler/config
# ---------------------------------------------------------------------------


@router.put(
    "/config",
    response_model=SchedulerStatus,
    summary="Update scheduler configuration",
)
async def update_scheduler_config(
    body: SchedulerConfigUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> SchedulerStatus:
    """Update the scheduler's ``interval_hours`` setting.

    Accepts values between 1 and 168 (1 hour to 1 week).  Returns the
    updated ``SchedulerStatus``.

    Raises:
        AuthError (HTTP 401): if the request is not authenticated.
        NotFoundError (HTTP 404): if the scheduler config row is missing.
        ValidationError (HTTP 422): if ``interval_hours`` is out of range
            (enforced by Pydantic before this handler is called).
    """
    config = await _get_scheduler_config(db)
    config.interval_hours = body.interval_hours
    await db.flush()
    return _config_to_status(config)
