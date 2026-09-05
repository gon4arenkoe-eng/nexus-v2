"""SQLAlchemy persistence base for NEXUS V2 infrastructure."""

from sqlalchemy.orm import DeclarativeBase


class PersistenceBase(DeclarativeBase):
    """Canonical SQLAlchemy declarative base for V2 persistence."""

    pass
