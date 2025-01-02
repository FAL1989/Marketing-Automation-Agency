"""
Configuração da sessão do banco de dados
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import logging

from app.core.config import Settings

logger = logging.getLogger(__name__)

settings = Settings()

# Cria o engine do SQLAlchemy
engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    **settings.SQLALCHEMY_ENGINE_OPTIONS
)

# Cria a fábrica de sessões
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency para obter uma sessão do banco de dados
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Erro na sessão do banco de dados: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

__all__ = ["AsyncSessionLocal", "engine", "get_db"] 