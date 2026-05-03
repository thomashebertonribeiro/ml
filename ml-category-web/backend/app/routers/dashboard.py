"""
Dashboard router.

Endpoints (all require authentication):
    GET /dashboard/stats  — aggregated statistics with Redis cache (5 min)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, get_redis
from app.models.category import Category
from app.models.change_log import ChangeLog
from app.models.import_job import ImportJob
from app.models.user import User
from app.schemas.dashboard import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_CACHE_KEY = "dashboard:stats"
_CACHE_TTL = 300  # 5 minutes


# ---------------------------------------------------------------------------
# GET /dashboard/stats
# ---------------------------------------------------------------------------


@router.get(
    "/stats",
    response_model=DashboardStats,
    summary="Get aggregated dashboard statistics",
)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),  # type: ignore[type-arg]
    _current_user: User = Depends(get_current_user),
) -> DashboardStats:
    """Return aggregated statistics about the category database.

    The result is cached in Redis under the key ``"dashboard:stats"`` for
    5 minutes to avoid repeated heavy queries.

    Fields returned:
        total_categories: total number of categories
        total_root_categories: categories with no parent (level 0)
        total_leaf_categories: categories that have no children
        max_depth: maximum ``level`` value across all categories
        last_import_at: ``started_at`` of the most recent completed ImportJob
        changes_last_30_days: ChangeLog entries in the last 30 days
        categories_by_level: mapping of {level: count}
    """
    # Try cache first
    try:
        raw = await redis.get(_CACHE_KEY)
        if raw is not None:
            data = json.loads(raw)
            return DashboardStats.model_validate(data)
    except Exception:  # noqa: BLE001
        pass  # Cache miss or Redis error — fall through to DB

    stats = await _compute_stats(db)

    # Store in cache
    try:
        payload = stats.model_dump()
        # Convert datetime to ISO string for JSON serialisation
        if payload.get("last_import_at") is not None:
            payload["last_import_at"] = payload["last_import_at"].isoformat()
        await redis.set(_CACHE_KEY, json.dumps(payload), ex=_CACHE_TTL)
    except Exception:  # noqa: BLE001
        pass  # Cache write failure is non-fatal

    return stats


# ---------------------------------------------------------------------------
# Internal computation
# ---------------------------------------------------------------------------


async def _compute_stats(db: AsyncSession) -> DashboardStats:
    """Query the database and build a ``DashboardStats`` instance."""

    # 1. total_categories
    total_result = await db.execute(select(func.count()).select_from(Category))
    total_categories: int = total_result.scalar_one() or 0

    # 2. total_root_categories (parent_id IS NULL)
    root_result = await db.execute(
        select(func.count()).select_from(Category).where(Category.parent_id.is_(None))
    )
    total_root_categories: int = root_result.scalar_one() or 0

    # 3. total_leaf_categories — categories that have no children
    #    A category is a leaf if its id does not appear as parent_id in any row.
    leaf_subquery = (
        select(Category.parent_id)
        .where(Category.parent_id.is_not(None))
        .distinct()
        .scalar_subquery()
    )
    leaf_result = await db.execute(
        select(func.count())
        .select_from(Category)
        .where(Category.id.not_in(leaf_subquery))
    )
    total_leaf_categories: int = leaf_result.scalar_one() or 0

    # 4. max_depth
    depth_result = await db.execute(select(func.max(Category.level)))
    max_depth: int = depth_result.scalar_one() or 0

    # 5. last_import_at — started_at of the most recent completed ImportJob
    import_result = await db.execute(
        select(ImportJob.started_at)
        .where(ImportJob.status == "completed")
        .order_by(ImportJob.started_at.desc())
        .limit(1)
    )
    last_import_at: datetime | None = import_result.scalar_one_or_none()

    # 6. changes_last_30_days
    cutoff_30d = datetime.now(tz=timezone.utc) - timedelta(days=30)
    changes_result = await db.execute(
        select(func.count())
        .select_from(ChangeLog)
        .where(ChangeLog.detected_at >= cutoff_30d)
    )
    changes_last_30_days: int = changes_result.scalar_one() or 0

    # 7. categories_by_level — {level: count}
    level_result = await db.execute(
        select(Category.level, func.count().label("cnt"))
        .group_by(Category.level)
        .order_by(Category.level)
    )
    categories_by_level: dict[int, int] = {
        row.level: row.cnt for row in level_result.all()
    }

    return DashboardStats(
        total_categories=total_categories,
        total_root_categories=total_root_categories,
        total_leaf_categories=total_leaf_categories,
        max_depth=max_depth,
        last_import_at=last_import_at,
        changes_last_30_days=changes_last_30_days,
        categories_by_level=categories_by_level,
    )
