"""DatabaseManager — gerencia o ciclo de vida da conexão SQLite e as migrações de schema."""

from __future__ import annotations

import os
import sqlite3

DEFAULT_DB_PATH = os.path.expanduser("~/.mercadolivre-browser/categories.db")

_DDL = """
CREATE TABLE IF NOT EXISTS categories (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    parent_id   TEXT REFERENCES categories(id) ON DELETE SET NULL,
    level       INTEGER NOT NULL DEFAULT 0,
    total_items INTEGER NOT NULL DEFAULT 0,
    path_json   TEXT NOT NULL DEFAULT '[]',
    updated_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_categories_parent_id ON categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_categories_name      ON categories(name COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_categories_updated   ON categories(updated_at);

CREATE TABLE IF NOT EXISTS app_config (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


class DatabaseManager:
    """Manages the SQLite connection lifecycle and schema migrations.

    Args:
        db_path: Path to the SQLite database file.
                 Defaults to ``~/.mercadolivre-browser/categories.db``.
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        self._db_path = db_path
        self._connection: sqlite3.Connection | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Create tables and indexes if they do not exist; run migrations.

        Also ensures the parent directory exists before opening the file.
        """
        parent_dir = os.path.dirname(self._db_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        conn = self.get_connection()
        conn.executescript(_DDL)
        conn.commit()

    def get_connection(self) -> sqlite3.Connection:
        """Return a thread-safe SQLite connection, creating it if necessary.

        The connection is configured with:
        - ``check_same_thread=False`` for multi-thread access
        - WAL journal mode for better write concurrency
        - Foreign key enforcement
        """
        if self._connection is None:
            self._connection = sqlite3.connect(
                self._db_path,
                check_same_thread=False,
            )
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA journal_mode=WAL")
            self._connection.execute("PRAGMA foreign_keys=ON")
        return self._connection

    def close(self) -> None:
        """Close the underlying SQLite connection if it is open."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
