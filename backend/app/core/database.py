"""Database session and engine management."""

from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""
    pass


# Sync Engine & Session (Alembic, seed scripts, sync migrations)
sync_engine = create_engine(
    settings.sync_database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# Async Engine & Session (FastAPI routes & async services)
async_engine = create_async_engine(
    settings.async_database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_sync_db() -> Generator[Session, None, None]:
    """Dependency for synchronous database session."""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for asynchronous database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
