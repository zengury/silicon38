"""
Database engine factory with connection pooling.

Creates a SQLAlchemy engine from settings.DATABASE_URL.  Pool parameters
are skipped for SQLite to avoid errors with its SingletonThreadPool.

Exports:
    engine: SQLAlchemy Engine singleton
    DATABASE_URL: Current connection string
    DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_TIMEOUT, DB_POOL_RECYCLE, DB_ECHO
"""

from sqlmodel import create_engine, SQLModel

from core.config import settings

DATABASE_URL = settings.DATABASE_URL
DB_POOL_SIZE = settings.DB_POOL_SIZE
DB_MAX_OVERFLOW = settings.DB_MAX_OVERFLOW
DB_POOL_TIMEOUT = settings.DB_POOL_TIMEOUT
DB_POOL_RECYCLE = settings.DB_POOL_RECYCLE
DB_ECHO = settings.DB_ECHO

_IS_SQLITE = DATABASE_URL.startswith("sqlite")

if _IS_SQLITE:
    # SQLite uses SingletonThreadPool — pool args are not supported
    engine = create_engine(
        DATABASE_URL,
        echo=DB_ECHO,
        connect_args={"check_same_thread": False} if _IS_SQLITE else {},
    )
else:
    engine = create_engine(
        DATABASE_URL,
        echo=DB_ECHO,
        pool_size=DB_POOL_SIZE,
        max_overflow=DB_MAX_OVERFLOW,
        pool_timeout=DB_POOL_TIMEOUT,
        pool_recycle=DB_POOL_RECYCLE,
    )


def get_engine():
    """Return the SQLAlchemy engine (useful for health checks)."""
    return engine
