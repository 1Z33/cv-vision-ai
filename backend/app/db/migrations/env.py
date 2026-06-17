"""Alembic environment configuration.

This repo uses Alembic to manage schema changes for SQLAlchemy models.
"""

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.db.base import Base
from app.core.config import settings


# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Provide metadata for 'autogenerate'
target_metadata = Base.metadata


def _set_sqlalchemy_url() -> None:
    """Ensure alembic knows the DB URL.

    Priority:
      1) ALEMBIC_DATABASE_URL (env var override)
      2) settings.SYNC_DATABASE_URL
      3) settings.DATABASE_URL (fallback; may already be sync or async)
    """
    url = os.getenv("ALEMBIC_DATABASE_URL")
    if not url:
        url = getattr(settings, "SYNC_DATABASE_URL", None) or getattr(settings, "DATABASE_URL", None)

    if not url:
        raise RuntimeError(
            "Missing database URL (expected ALEMBIC_DATABASE_URL or SYNC_DATABASE_URL or DATABASE_URL in settings)."
        )

    config.set_main_option("sqlalchemy.url", url)



def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    _set_sqlalchemy_url()
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


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (sync engine).

    This project appears to use a synchronous Postgres driver (psycopg2).
    Using an async SQLAlchemy engine would fail because the async extension
    requires an async driver (asyncpg).
    """
    _set_sqlalchemy_url()

    from sqlalchemy import engine_from_config

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)



if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

