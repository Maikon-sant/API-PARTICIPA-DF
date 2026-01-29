"""
Sessão async do SQLAlchemy e factory de dependência.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.infrastructure.db.base import Base
from app.infrastructure.db.models import AttachmentModel, ManifestationModel  # noqa: F401

_settings = get_settings()
_engine = create_async_engine(
    _settings.database_url,
    echo=_settings.debug,
)
_async_session_factory = async_sessionmaker(
    _engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependência FastAPI: fornece sessão async por request."""
    async with _async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Cria tabelas (útil para testes; em produção use Alembic)."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
