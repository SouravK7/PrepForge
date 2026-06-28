"""
Database initialization and session management.

Handles database creation, table initialization,
and provides session factory for repository use.
"""

from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from database.models import Base


def _get_database_url() -> str:
    """
    Get database URL from environment or config.

    Returns:
        Database URL string.
    """
    db_url = os.getenv(
        "DATABASE_URL",
        "sqlite:///interview_assistant.db",
    )
    return db_url


# Create engine
database_url = _get_database_url()
engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
    echo=False,
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def init_db() -> None:
    """
    Initialize the database by creating all tables.

    Creates all tables defined in models.py if they
    do not already exist. Safe to call multiple times.

    Raises:
        SQLAlchemyError: If table creation fails.
    """
    print("Initializing database...")
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized: {database_url}")


def drop_db() -> None:
    """
    Drop all database tables.

    WARNING: Destroys all data. Use only for testing.
    """
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped.")


def get_session() -> Generator[Session, None, None]:
    """
    Provide a database session as a context manager.

    Used as a dependency in FastAPI routes and services.
    Automatically closes session after use.

    Yields:
        SQLAlchemy Session.

    Example:
        with get_session() as session:
            repo = UserRepository(session)
            user = repo.get_by_id(1)
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def health_check() -> bool:
    """
    Check if database is reachable.

    Returns:
        True if database is healthy, False otherwise.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
