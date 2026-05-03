"""
Alembic environment configuration.

Configured for async SQLAlchemy engine (asyncpg driver).
All ORM models are imported here so that Alembic can detect schema changes
via autogenerate.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ---------------------------------------------------------------------------
# Import all models so their metadata is registered on Base.metadata
# ---------------------------------------------------------------------------
from app.database import Base  # noqa: F401 — registers DeclarativeBase
from app.models import (  # noqa: F401 — registers all table metadata
    Category,
    ChangeLog,
    ImportJob,
    SchedulerConfig,
    User,
)

# ---------------------------------------------------------------------------
# Alembic Config object — provides access to values in alembic.ini
# ---------------------------------------------------------------------------
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url from the application settings so we never
# hard-code credentials in alembic.ini.
try:
    from app.config import settings

    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
except Exception:
    # Allow alembic to run without a .env file (e.g., in CI with env vars)
    pass

# Metadata object used for autogenerate support
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline migrations (generate SQL without a live DB connection)
# ---------------------------------------------------------------------------


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine, though
    an Engine is acceptable here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migrations (run against a live async DB connection)
# ---------------------------------------------------------------------------


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations within a sync-compatible wrapper."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async engine."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
