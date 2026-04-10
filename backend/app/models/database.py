from sqlalchemy.orm import DeclarativeBase
from loguru import logger


class Base(DeclarativeBase):
    pass


# Lazy initialization — only connect when actually needed
_engine = None
_async_session = None


def _init_engine():
    global _engine, _async_session
    if _engine is not None:
        return

    try:
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
        from app.config import get_settings
        settings = get_settings()

        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            pool_size=20,
            max_overflow=10,
        )
        _async_session = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
        logger.info("Database engine initialized")
    except Exception as e:
        logger.warning(f"Database not available: {e}. Running without DB.")


def get_engine():
    _init_engine()
    return _engine


async def get_db():
    _init_engine()
    if _async_session is None:
        raise RuntimeError("Database not configured")
    async with _async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    _init_engine()
    if _engine is None:
        logger.warning("Skipping DB init — no engine available")
        return
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
