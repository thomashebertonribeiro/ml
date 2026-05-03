"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

Creates all tables, indexes, and seeds the scheduler_config singleton row.
Requires PostgreSQL extensions: pgcrypto (gen_random_uuid) and pg_trgm (GIN index).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # PostgreSQL extensions
    # ------------------------------------------------------------------
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # ------------------------------------------------------------------
    # Table: users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    # ------------------------------------------------------------------
    # Table: categories
    # ------------------------------------------------------------------
    op.create_table(
        "categories",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("parent_id", sa.Text(), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "path_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="'[]'::jsonb",
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["categories.id"],
            name="fk_categories_parent_id",
            ondelete="SET NULL",
        ),
    )

    op.create_index("idx_categories_parent_id", "categories", ["parent_id"])
    op.create_index("idx_categories_level", "categories", ["level"])
    # GIN index for trigram-based full-text search on category names
    op.create_index(
        "idx_categories_name_trgm",
        "categories",
        ["name"],
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )

    # ------------------------------------------------------------------
    # Table: import_jobs
    # ------------------------------------------------------------------
    op.create_table(
        "import_jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_estimated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("finished_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "triggered_by",
            sa.Text(),
            nullable=False,
            server_default="manual",
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed')",
            name="ck_import_jobs_status",
        ),
        sa.CheckConstraint(
            "triggered_by IN ('manual', 'scheduler')",
            name="ck_import_jobs_triggered_by",
        ),
    )

    op.create_index("idx_import_jobs_status", "import_jobs", ["status"])
    op.create_index(
        "idx_import_jobs_created_at",
        "import_jobs",
        [sa.text("created_at DESC")],
    )

    # ------------------------------------------------------------------
    # Table: change_log
    # ------------------------------------------------------------------
    op.create_table(
        "change_log",
        sa.Column(
            "id",
            sa.BigInteger(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("change_type", sa.Text(), nullable=False),
        sa.Column("category_id", sa.Text(), nullable=False),
        sa.Column("category_name", sa.Text(), nullable=False),
        sa.Column("parent_id", sa.Text(), nullable=True),
        sa.Column(
            "detected_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "import_job_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.CheckConstraint(
            "change_type IN ('added', 'removed')",
            name="ck_change_log_change_type",
        ),
        sa.ForeignKeyConstraint(
            ["import_job_id"],
            ["import_jobs.id"],
            name="fk_change_log_import_job_id",
            ondelete="CASCADE",
        ),
    )

    op.create_index(
        "idx_change_log_detected_at",
        "change_log",
        [sa.text("detected_at DESC")],
    )
    op.create_index("idx_change_log_category_id", "change_log", ["category_id"])
    op.create_index("idx_change_log_change_type", "change_log", ["change_type"])
    op.create_index("idx_change_log_import_job_id", "change_log", ["import_job_id"])

    # ------------------------------------------------------------------
    # Table: scheduler_config  (singleton, id must always be 1)
    # ------------------------------------------------------------------
    op.create_table(
        "scheduler_config",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("interval_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_run_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("next_run_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_run_result", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.CheckConstraint("id = 1", name="ck_scheduler_config_singleton"),
        sa.CheckConstraint(
            "interval_hours BETWEEN 1 AND 168",
            name="ck_scheduler_config_interval_hours",
        ),
    )

    # Seed: ensure the singleton row always exists
    op.execute(
        "INSERT INTO scheduler_config (id) VALUES (1) ON CONFLICT DO NOTHING"
    )


def downgrade() -> None:
    op.drop_table("scheduler_config")
    op.drop_index("idx_change_log_import_job_id", table_name="change_log")
    op.drop_index("idx_change_log_change_type", table_name="change_log")
    op.drop_index("idx_change_log_category_id", table_name="change_log")
    op.drop_index("idx_change_log_detected_at", table_name="change_log")
    op.drop_table("change_log")
    op.drop_index("idx_import_jobs_created_at", table_name="import_jobs")
    op.drop_index("idx_import_jobs_status", table_name="import_jobs")
    op.drop_table("import_jobs")
    op.drop_index("idx_categories_name_trgm", table_name="categories")
    op.drop_index("idx_categories_level", table_name="categories")
    op.drop_index("idx_categories_parent_id", table_name="categories")
    op.drop_table("categories")
    op.drop_table("users")
