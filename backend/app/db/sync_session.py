"""
Configuração da sessão síncrona do banco de dados para o Alembic
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..core.config import settings

# Criar engine síncrono do SQLAlchemy
sync_engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI).replace("postgresql+asyncpg", "postgresql+psycopg2"),
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_size=settings.SQLALCHEMY_POOL_SIZE,
    max_overflow=settings.SQLALCHEMY_MAX_OVERFLOW,
    pool_timeout=settings.SQLALCHEMY_POOL_TIMEOUT,
)

# Criar fábrica de sessões síncrona
SyncSessionLocal = sessionmaker(
    sync_engine,
    autocommit=False,
    autoflush=False,
)

__all__ = ["SyncSessionLocal", "sync_engine"] 