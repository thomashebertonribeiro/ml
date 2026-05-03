"""CategoryRepository — abstrai todas as operações de leitura e escrita no SQLite."""

from __future__ import annotations

import csv
import json
import threading
from datetime import datetime, timezone
from typing import Optional

from src.models.category import CategoryDTO
from src.repository.database import DatabaseManager


def _row_to_dto(row) -> CategoryDTO:
    """Convert a sqlite3.Row to a CategoryDTO."""
    path_from_root = json.loads(row["path_json"]) if row["path_json"] else []
    updated_at_str = row["updated_at"]
    try:
        # Normaliza para naive UTC removendo offset/Z
        clean = updated_at_str.rstrip("Z").split("+")[0]
        updated_at = datetime.fromisoformat(clean)
    except (ValueError, TypeError):
        updated_at = datetime.utcnow()

    return CategoryDTO(
        id=row["id"],
        name=row["name"],
        parent_id=row["parent_id"],
        level=row["level"],
        total_items_in_this_category=row["total_items"],
        path_from_root=path_from_root,
        children_ids=[],  # derived via get_children()
        updated_at=updated_at,
    )


class CategoryRepository:
    """Abstracts all read/write operations on the SQLite categories table.

    Args:
        db_manager: A :class:`DatabaseManager` instance (or a db_path string
                    for convenience — a ``DatabaseManager`` will be created
                    and initialized automatically).
    """

    def __init__(self, db_manager: DatabaseManager | str) -> None:
        if isinstance(db_manager, str):
            db_manager = DatabaseManager(db_manager)
            db_manager.initialize()
        self._db = db_manager
        self._write_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def upsert(self, category: CategoryDTO) -> None:
        """Insert or replace a category (deduplication via INSERT OR REPLACE).

        ``path_from_root`` is serialized as a JSON string in the ``path_json``
        column.  ``children_ids`` is NOT stored — it is derived via
        :meth:`get_children`.

        ``updated_at`` is stored as an ISO 8601 UTC string.
        """
        path_json = json.dumps(category.path_from_root)
        # Normalise updated_at to UTC ISO 8601 string
        updated_at = category.updated_at
        if updated_at.tzinfo is None:
            # Treat naive datetimes as UTC
            updated_at_str = updated_at.isoformat() + "Z"
        else:
            updated_at_str = updated_at.astimezone(timezone.utc).isoformat()

        with self._write_lock:
            conn = self._db.get_connection()
            conn.execute(
                """
                INSERT OR REPLACE INTO categories
                    (id, name, parent_id, level, total_items, path_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    category.id,
                    category.name,
                    category.parent_id,
                    category.level,
                    category.total_items_in_this_category,
                    path_json,
                    updated_at_str,
                ),
            )
            conn.commit()

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_by_id(self, category_id: str) -> Optional[CategoryDTO]:
        """Return the category with the given id, or ``None`` if not found."""
        conn = self._db.get_connection()
        row = conn.execute(
            "SELECT * FROM categories WHERE id = ?", (category_id,)
        ).fetchone()
        if row is None:
            return None
        return _row_to_dto(row)

    def get_children(self, parent_id: Optional[str]) -> list[CategoryDTO]:
        """Return direct children of *parent_id*.

        When *parent_id* is ``None``, returns root categories (those whose
        ``parent_id`` IS NULL in the database).
        """
        conn = self._db.get_connection()
        if parent_id is None:
            rows = conn.execute(
                "SELECT * FROM categories WHERE parent_id IS NULL"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM categories WHERE parent_id = ?", (parent_id,)
            ).fetchall()
        return [_row_to_dto(r) for r in rows]

    def get_all(self) -> list[CategoryDTO]:
        """Return all categories stored in the database."""
        conn = self._db.get_connection()
        rows = conn.execute("SELECT * FROM categories").fetchall()
        return [_row_to_dto(r) for r in rows]

    def is_stale(self, category_id: str, max_age_hours: int = 24) -> bool:
        """Return ``True`` if the category's ``updated_at`` is older than *max_age_hours*.

        Returns ``True`` when the category does not exist (treat missing data
        as stale so it will be fetched from the API).
        """
        conn = self._db.get_connection()
        row = conn.execute(
            "SELECT updated_at FROM categories WHERE id = ?", (category_id,)
        ).fetchone()
        if row is None:
            return True

        updated_at_str: str = row["updated_at"]
        try:
            # Remove 'Z' e offset para manter naive UTC consistente
            updated_at_str_clean = updated_at_str.rstrip("Z").split("+")[0]
            updated_at = datetime.fromisoformat(updated_at_str_clean)
        except (ValueError, TypeError):
            return True

        # Normaliza para comparação: garante que ambos sejam naive UTC
        if updated_at.tzinfo is not None:
            updated_at = updated_at.astimezone(timezone.utc).replace(tzinfo=None)
        now = datetime.utcnow()
        age_hours = (now - updated_at).total_seconds() / 3600
        return age_hours > max_age_hours

    def search_local(self, query: str) -> list[CategoryDTO]:
        """Case-insensitive search by name using SQL LIKE.

        Args:
            query: Substring to search for in category names.

        Returns:
            List of matching :class:`CategoryDTO` objects.
        """
        conn = self._db.get_connection()
        pattern = f"%{query}%"
        rows = conn.execute(
            "SELECT * FROM categories WHERE name LIKE ? COLLATE NOCASE",
            (pattern,),
        ).fetchall()
        return [_row_to_dto(r) for r in rows]

    # ------------------------------------------------------------------
    # Export operations
    # ------------------------------------------------------------------

    def export_json(self, path: str) -> None:
        """Export all categories to a JSON file at *path*.

        The file contains a JSON array of dicts with all fields.
        """
        categories = self.get_all()
        data = [cat.to_dict() for cat in categories]
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2, default=str)

    def export_csv(self, path: str) -> None:
        """Export all categories to a CSV file at *path*.

        Header: ``id,name,parent_id,level,total_items,updated_at``
        """
        categories = self.get_all()
        fieldnames = ["id", "name", "parent_id", "level", "total_items", "updated_at"]
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for cat in categories:
                updated_at = cat.updated_at
                if isinstance(updated_at, datetime):
                    updated_at_str = updated_at.isoformat()
                else:
                    updated_at_str = str(updated_at)
                writer.writerow(
                    {
                        "id": cat.id,
                        "name": cat.name,
                        "parent_id": cat.parent_id if cat.parent_id is not None else "",
                        "level": cat.level,
                        "total_items": cat.total_items_in_this_category,
                        "updated_at": updated_at_str,
                    }
                )
