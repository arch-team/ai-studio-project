"""Database configuration - SQLAlchemy 2.0 async setup."""

from collections.abc import AsyncGenerator

import structlog
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.shared.infrastructure.config import get_settings

logger = structlog.get_logger(__name__)


def import_all_models() -> None:
    """Import all ORM models to ensure proper SQLAlchemy mapper registration.

    This must be called before using any ORM relationships that use string references.
    """
    # Auth module models
    # Audit module models
    from src.modules.audit.infrastructure.models import AuditLogModel  # noqa: F401
    from src.modules.auth.infrastructure.models import LoginAttemptModel, UserModel  # noqa: F401

    # Datasets module models
    from src.modules.datasets.infrastructure.models import DatasetModel  # noqa: F401

    # Models module models
    from src.modules.models.infrastructure.models import ModelModel  # noqa: F401

    # Quotas module models
    from src.modules.quotas.infrastructure.models import (  # noqa: F401
        ResourceLimitConfigModel,
        ResourceQuotaModel,
    )

    # Spaces module models
    from src.modules.spaces.infrastructure.models import DevelopmentSpaceModel  # noqa: F401

    # Training module models
    from src.modules.training.infrastructure.models import (  # noqa: F401
        CheckpointModel,
        TrainingJobModel,
    )

    logger.debug("orm_models_imported")


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""

    pass


def create_engine() -> AsyncEngine:
    """Create async SQLAlchemy engine."""
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=settings.debug,
    )


engine = create_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.warning("database_transaction_rollback", error_type=type(e).__name__, error=str(e))
            await session.rollback()
            raise
        finally:
            await session.close()


__all__ = ["Base", "engine", "AsyncSessionLocal", "get_db", "import_all_models"]
