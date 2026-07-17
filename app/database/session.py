"""
Async SQLAlchemy engine + session factory.
Also handles auto-creating the target MySQL database if it does not exist yet,
since app-level DDL only creates tables inside an existing schema.
"""
import pymysql
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings
from app.utils.logger import logger


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


def ensure_database_exists() -> None:
    """
    Connects to MySQL WITHOUT selecting a database and creates the
    target database if it doesn't already exist. Uses a synchronous
    pymysql connection since this runs once at startup before the
    async engine/pool is created.
    """
    conn = pymysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{settings.mysql_database}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
        logger.info(f"Verified/created database '{settings.mysql_database}'")
    finally:
        conn.close()


engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """FastAPI dependency that yields a request-scoped async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_models() -> None:
    """Create all tables that don't exist yet. Alembic should be used for
    real migrations in production; this is a convenience for first boot/dev."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
