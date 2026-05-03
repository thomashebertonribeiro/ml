"""
Category service — business logic for category queries and persistence.

All functions are async and accept an ``AsyncSession`` from SQLAlchemy.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------


async def get_root_categories(db: AsyncSession) -> list[Category]:
    """Return all root categories (parent_id IS NULL) ordered by name."""
    result = await db.execute(
        select(Category)
        .where(Category.parent_id.is_(None))
        .order_by(Category.name)
    )
    return list(result.scalars().all())


async def get_category_by_id(db: AsyncSession, category_id: str) -> Category | None:
    """Return a single category by its primary key, or None if not found.

    Eagerly loads the ``children`` relationship so callers can build
    ``CategoryDetail`` responses without issuing extra queries.
    """
    result = await db.execute(
        select(Category)
        .where(Category.id == category_id)
        .options(selectinload(Category.children))
    )
    return result.scalar_one_or_none()


async def get_children(db: AsyncSession, parent_id: str) -> list[Category]:
    """Return direct children of *parent_id* ordered by name."""
    result = await db.execute(
        select(Category)
        .where(Category.parent_id == parent_id)
        .order_by(Category.name)
    )
    return list(result.scalars().all())


async def search_categories(
    db: AsyncSession,
    query: str,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Category], int]:
    """Search categories by name using a case-insensitive ILIKE pattern.

    Args:
        db: Async SQLAlchemy session.
        query: Search term (must be at least 2 characters — enforced by the
            router layer, not here).
        page: 1-based page number.
        page_size: Maximum number of items per page.

    Returns:
        A tuple of ``(items, total)`` where *total* is the count of all
        matching rows (before pagination).
    """
    pattern = f"%{query}%"
    base_filter = Category.name.ilike(pattern)

    # Total count
    count_result = await db.execute(
        select(func.count()).select_from(Category).where(base_filter)
    )
    total: int = count_result.scalar_one()

    # Paginated items
    offset = (page - 1) * page_size
    items_result = await db.execute(
        select(Category)
        .where(base_filter)
        .order_by(Category.name)
        .offset(offset)
        .limit(page_size)
    )
    items = list(items_result.scalars().all())

    return items, total


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


async def upsert_category(db: AsyncSession, data: dict) -> Category:
    """Insert or update a category using SQLAlchemy's ``merge`` (upsert).

    Expected keys in *data*:
        - ``id`` (str, required)
        - ``name`` (str, required)
        - ``parent_id`` (str | None)
        - ``level`` (int)
        - ``total_items`` (int)
        - ``path_json`` (list)
        - ``updated_at`` (datetime, optional — defaults to now UTC)

    Returns:
        The merged (and session-tracked) ``Category`` instance.
    """
    now = datetime.now(tz=timezone.utc)

    category = Category(
        id=data["id"],
        name=data["name"],
        parent_id=data.get("parent_id"),
        level=data.get("level", 0),
        total_items=data.get("total_items", 0),
        path_json=data.get("path_json", []),
        updated_at=data.get("updated_at", now),
    )

    # merge performs INSERT if the PK is absent, UPDATE otherwise
    merged: Category = await db.merge(category)
    await db.flush()
    return merged
