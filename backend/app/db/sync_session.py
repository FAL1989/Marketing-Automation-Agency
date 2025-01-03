"""
Configuração da sessão síncrona do banco de dados para o Alembic
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..core.config import settings

# Criar engine síncrono do SQLAlchemy
sync_engine = create_engine(
    str(settings.DATABASE_URL),
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False}  # Necessário para SQLite
)

# Criar fábrica de sessões síncrona
SyncSessionLocal = sessionmaker(
    sync_engine,
    autocommit=False,
    autoflush=False,
)

__all__ = ["SyncSessionLocal", "sync_engine"] 