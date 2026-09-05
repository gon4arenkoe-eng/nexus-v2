"""Async SQLAlchemy session infrastructure for NEXUS V2."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_persistence_engine(
    database_url: str,
    *,
    echo: bool = False,
) -> AsyncEngine:
    if not isinstance(database_url, str) or not database_url.strip():
        raise ValueError("database_url must be non-empty")

    if not isinstance(echo, bool):
        raise ValueError("echo must be a bool")

    return create_async_engine(
        database_url.strip(),
        echo=echo,
        pool_pre_ping=True,
    )


def create_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    if not isinstance(engine, AsyncEngine):
        raise ValueError("engine must be an AsyncEngine")

    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


async def session_scope(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    if not isinstance(factory, async_sessionmaker):
        raise ValueError(
            "factory must be an async_sessionmaker"
        )

    async with factory() as session:
        yield session
