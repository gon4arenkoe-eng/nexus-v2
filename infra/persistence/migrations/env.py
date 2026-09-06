"""Alembic environment for NEXUS V2 persistence."""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from infra.persistence.base import PersistenceBase


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = PersistenceBase.metadata


def _database_url() -> str:
    value = os.getenv("NEXUS_DATABASE_URL")

    if value is None or not value.strip():
        raise RuntimeError(
            "NEXUS_DATABASE_URL is required for online migrations"
        )

    return value.strip()


def run_migrations_offline() -> None:
    """Run migrations without opening a database connection."""

    url = os.getenv(
        "NEXUS_DATABASE_URL",
        "postgresql+asyncpg://offline.invalid/nexus",
    )

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def _run_migrations(connection: Connection) -> None:
    """Configure and run Alembic on a synchronous connection facade."""

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def _run_async_migrations() -> None:
    """Run online migrations through the configured async DBAPI."""

    configuration = config.get_section(
        config.config_ini_section,
        {},
    )
    configuration["sqlalchemy.url"] = _database_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    try:
        async with connectable.connect() as connection:
            await connection.run_sync(_run_migrations)
    finally:
        await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations against an explicitly configured database."""

    asyncio.run(_run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
