from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.pool import QueuePool
from ..core.config import settings
import structlog
import time
import random
from contextlib import asynccontextmanager
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import AsyncGenerator

logger = structlog.get_logger()

def create_db_engine():
    """Cria o engine assíncrono do SQLAlchemy com configurações otimizadas"""
    return create_async_engine(
        str(settings.SQLALCHEMY_DATABASE_URI),
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
        echo=settings.SQLALCHEMY_ECHO,
        future=True
    )

# Cria o engine do SQLAlchemy
engine = create_db_engine()

# Cria a fábrica de sessões com validação de conexão
SessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
async def get_db():
    """Fornece uma sessão do banco de dados com retry exponencial"""
    async with SessionLocal() as db:
        try:
            # Testa a conexão com retry usando text() explicitamente
            await db.execute(text("SELECT 1"))
            return db
        except (OperationalError, DBAPIError) as e:
            logger.error(
                "Erro de conexão com o banco",
                error=str(e),
                retry_count=1
            )
            await db.close()
            raise
        finally:
            await db.close()

@event.listens_for(Engine, "connect")
def connect(dbapi_connection, connection_record):
    """Configura a conexão quando ela é criada"""
    connection_record.info['pid'] = dbapi_connection.get_backend_pid()
    connection_record.info['created_at'] = time.time()

@event.listens_for(Engine, "checkout")
def checkout(dbapi_connection, connection_record, connection_proxy):
    """Verifica a conexão quando ela é retirada do pool"""
    pid = connection_record.info['pid']
    created_at = connection_record.info['created_at']
    age = time.time() - created_at
    
    logger.debug(
        "Conexão retirada do pool",
        pid=pid,
        age=age,
        pool_size=engine.pool.size(),
        checkedin=engine.pool.checkedin(),
        overflow=engine.pool.overflow()
    )
    
    # Recicla conexões antigas
    if age > 3600:  # 1 hora
        logger.info("Reciclando conexão antiga", pid=pid, age=age)
        return False  # Força a criação de uma nova conexão

@event.listens_for(Engine, "invalidate")
def invalidate(dbapi_connection, connection_record, exception):
    """Lida com conexões inválidas"""
    logger.warning(
        "Conexão invalidada",
        pid=connection_record.info.get('pid'),
        error=str(exception)
    ) 