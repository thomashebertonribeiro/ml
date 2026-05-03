"""
Changes router.

Endpoints (all require authentication):
    GET /changes?type=&category_id=&from_date=&to_date=&page=&page_size=
        — paginated ChangeLog list, ordered by detected_at DESC
    GET /changes/summary
        — monthly aggregation for the last 12 months
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.change_log import ChangeLog
from app.models.user import User
from app.schemas.change_log import ChangeLogOut, ChangeSummaryItem

router = APIRouter(prefix="/changes", tags=["changes"])


# ---------------------------------------------------------------------------
# GET /changes/summary  (must be declared BEFORE /{...} to avoid shadowing)
# ---------------------------------------------------------------------------


@router.get(
    "/summary",
    response_model=list[ChangeSummaryItem],
    summary="Monthly change summary for the last 12 months",
)
async def get_changes_summary(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[ChangeSummaryItem]:
    """Return a monthly aggregation of added/removed categories for the last
    12 calendar months (including the current month).

    Each item in the returned list has:
        - ``month``: ISO year-month string, e.g. ``"2024-01"``
        - ``added``: number of categories added that month
        - ``removed``: number of categories removed that month

    Months with no changes are included with counts of 0.
    """
    now = datetime.now(tz=timezone.utc)
    # Build the 12-month window: from the start of (now - 11 months) to now
    cutoff = (now.replace(day=1) - timedelta(days=1)).replace(day=1)
    # Go back 11 more months to get 12 total
    for _ in range(11):
        cutoff = (cutoff.replace(day=1) - timedelta(days=1)).replace(day=1)

    result = await db.execute(
        select(ChangeLog).where(ChangeLog.detected_at >= cutoff)
    )
    rows = list(result.scalars().all())

    # Aggregate in Python — avoids DB-specific date_trunc syntax issues
    # and keeps the query simple
    monthly: dict[str, dict[str, int]] = {}

    # Pre-populate all 12 months with zeros
    cursor = cutoff
    for _ in range(12):
        key = cursor.strftime("%Y-%m")
        monthly[key] = {"added": 0, "removed": 0}
        # Advance to next month
        if cursor.month == 12:
            cursor = cursor.replace(year=cursor.year + 1, month=1)
        else:
            cursor = cursor.replace(month=cursor.month + 1)

    for row in rows:
        detected = row.detected_at
        if detected.tzinfo is None:
            detected = detected.replace(tzinfo=timezone.utc)
        key = detected.strftime("%Y-%m")
        if key in monthly:
            monthly[key][row.change_type] += 1

    return [
        ChangeSummaryItem(month=month, added=counts["added"], removed=counts["removed"])
        for month, counts in sorted(monthly.items())
    ]


# ---------------------------------------------------------------------------
# GET /changes
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=dict,
    summary="List change log entries (paginated)",
)
async def list_changes(
    type: str | None = Query(None, description="Filter by change type: 'added' or 'removed'"),
    category_id: str | None = Query(None, description="Filter by category ID"),
    from_date: datetime | None = Query(None, description="Filter entries detected on or after this datetime (ISO 8601)"),
    to_date: datetime | None = Query(None, description="Filter entries detected on or before this datetime (ISO 8601)"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page (max 200)"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> dict:
    """Return a paginated list of ``ChangeLog`` entries, ordered by
    ``detected_at`` DESC.

    Optional filters:
        type: ``added`` or ``removed``
        category_id: exact match on ``category_id``
        from_date: lower bound on ``detected_at`` (inclusive)
        to_date: upper bound on ``detected_at`` (inclusive)

    Returns a dict with:
        items: list of ChangeLogOut
        total: total matching rows
        page: current page
        page_size: items per page
    """
    filters = []

    if type is not None:
        filters.append(ChangeLog.change_type == type)
    if category_id is not None:
        filters.append(ChangeLog.category_id == category_id)
    if from_date is not None:
        filters.append(ChangeLog.detected_at >= from_date)
    if to_date is not None:
        filters.append(ChangeLog.detected_at <= to_date)

    # Total count
    count_query = select(func.count()).select_from(ChangeLog)
    if filters:
        count_query = count_query.where(*filters)
    count_result = await db.execute(count_query)
    total: int = count_result.scalar_one()

    # Paginated items
    offset = (page - 1) * page_size
    items_query = (
        select(ChangeLog)
        .order_by(ChangeLog.detected_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    if filters:
        items_query = items_query.where(*filters)

    items_result = await db.execute(items_query)
    items = list(items_result.scalars().all())

    out_items = [
        ChangeLogOut(
            id=row.id,
            change_type=row.change_type,  # type: ignore[arg-type]
            category_id=row.category_id,
            category_name=row.category_name,
            parent_id=row.parent_id,
            detected_at=row.detected_at,
            import_job_id=str(row.import_job_id),
        )
        for row in items
    ]

    return {
        "items": out_items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
