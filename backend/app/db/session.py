from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


def get_engine_kwargs(db_uri: str) -> dict[str, Any]:
    """Assemble database engine kwargs conditionally based on dialect."""
    kwargs: dict[str, Any] = {
        "echo": settings.DB_ECHO,
        "future": True,
    }
    if db_uri.startswith("postgresql"):
        kwargs.update(
            {
                "pool_size": settings.DB_POOL_SIZE,
                "max_overflow": settings.DB_MAX_OVERFLOW,
                "pool_timeout": settings.DB_POOL_TIMEOUT,
                "pool_pre_ping": True,
            }
        )
    return kwargs


engine: AsyncEngine = create_async_engine(
    settings.async_database_uri,
    **get_engine_kwargs(settings.async_database_uri),
)

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for providing an asynchronous database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def check_db_connectivity() -> bool:
    """Verify live asynchronous database connectivity."""
    try:
        async with async_session_factory() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception:  # noqa: BLE001
        return False
