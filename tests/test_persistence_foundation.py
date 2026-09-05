import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from infra.persistence.base import PersistenceBase
from infra.persistence.session import (
    create_persistence_engine,
    create_session_factory,
)


def test_persistence_base_exists() -> None:
    assert PersistenceBase.metadata is not None


def test_async_engine_factory() -> None:
    engine = create_persistence_engine(
        "sqlite+aiosqlite:///:memory:"
    )

    assert isinstance(engine, AsyncEngine)


def test_empty_database_url_fails_closed() -> None:
    with pytest.raises(ValueError):
        create_persistence_engine("")


def test_session_factory_uses_async_engine() -> None:
    engine = create_persistence_engine(
        "sqlite+aiosqlite:///:memory:"
    )

    factory = create_session_factory(engine)

    assert factory.kw["bind"] is engine
