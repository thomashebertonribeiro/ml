"""
Export service — serializes the category tree to JSON or CSV.

Functions:
    export_json(db, root_id=None) -> str
    export_csv(db, root_id=None) -> str

Both functions raise ``NotFoundError`` when the database has no categories.
If ``root_id`` is provided, only the subtree rooted at that category is
exported (BFS traversal).
"""

from __future__ import annotations

import csv
import io
import json
from collections import deque

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.services.exceptions import NotFoundError


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _fetch_subtree(db: AsyncSession, root_id: str) -> list[Category]:
    """Return all categories in the subtree rooted at *root_id* (BFS order).

    The root category itself is included as the first element.

    Raises:
        NotFoundError: if *root_id* does not exist.
    """
    # Fetch root
    result = await db.execute(select(Category).where(Category.id == root_id))
    root = result.scalar_one_or_none()
    if root is None:
        raise NotFoundError(f"Categoria '{root_id}' não encontrada.")

    visited: list[Category] = []
    queue: deque[str] = deque([root_id])

    while queue:
        current_id = queue.popleft()
        result = await db.execute(
            select(Category).where(Category.id == current_id)
        )
        node = result.scalar_one_or_none()
        if node is None:
            continue
        visited.append(node)

        # Enqueue children
        children_result = await db.execute(
            select(Category).where(Category.parent_id == current_id).order_by(Category.name)
        )
        for child in children_result.scalars().all():
            queue.append(child.id)

    return visited


async def _fetch_all(db: AsyncSession) -> list[Category]:
    """Return all categories ordered by level then name."""
    result = await db.execute(
        select(Category).order_by(Category.level, Category.name)
    )
    return list(result.scalars().all())


def _category_to_dict(cat: Category) -> dict:
    """Convert a Category ORM instance to a plain dict for JSON export."""
    return {
        "id": cat.id,
        "name": cat.name,
        "parent_id": cat.parent_id,
        "level": cat.level,
        "total_items": cat.total_items,
        "path_from_root": cat.path_json or [],
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def export_json(db: AsyncSession, root_id: str | None = None) -> str:
    """Serialize categories to a JSON string.

    Args:
        db: Async SQLAlchemy session.
        root_id: If provided, export only the subtree rooted at this category
            (BFS order). If ``None``, export all categories.

    Returns:
        A JSON-encoded string representing a list of category objects.
        Each object has the fields: ``id``, ``name``, ``parent_id``,
        ``level``, ``total_items``, ``path_from_root``.

    Raises:
        NotFoundError: if the database has no categories, or if *root_id*
            is provided but does not exist.
    """
    if root_id is not None:
        categories = await _fetch_subtree(db, root_id)
    else:
        categories = await _fetch_all(db)

    if not categories:
        raise NotFoundError("Não há categorias para exportar.")

    data = [_category_to_dict(cat) for cat in categories]
    return json.dumps(data, ensure_ascii=False, indent=2)


async def export_csv(db: AsyncSession, root_id: str | None = None) -> str:
    """Serialize categories to a CSV string.

    Args:
        db: Async SQLAlchemy session.
        root_id: If provided, export only the subtree rooted at this category
            (BFS order). If ``None``, export all categories.

    Returns:
        A CSV-encoded string with header row:
        ``id,name,parent_id,level,total_items,updated_at``

    Raises:
        NotFoundError: if the database has no categories, or if *root_id*
            is provided but does not exist.
    """
    if root_id is not None:
        categories = await _fetch_subtree(db, root_id)
    else:
        categories = await _fetch_all(db)

    if not categories:
        raise NotFoundError("Não há categorias para exportar.")

    output = io.StringIO()
    fieldnames = ["id", "name", "parent_id", "level", "total_items", "updated_at"]
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()

    for cat in categories:
        writer.writerow(
            {
                "id": cat.id,
                "name": cat.name,
                "parent_id": cat.parent_id if cat.parent_id is not None else "",
                "level": cat.level,
                "total_items": cat.total_items,
                "updated_at": cat.updated_at.isoformat() if cat.updated_at else "",
            }
        )

    return output.getvalue()
