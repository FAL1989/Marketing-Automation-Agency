"""
Configuração da sessão do banco de dados
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import logging
from pathlib import Path
from sqlalchemy.pool import AsyncAdaptedQueuePool
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log

from app.core.config import settings
from app.monitoring.pool_metrics import (
    track_connection_time,
    track_query_time,
    update_pool_metrics,
    record_connection_error,
    record_retry_attempt
)

logger = logging.getLogger(__name__)

# Garante que o diretório do banco existe
db_path = Path("./data")
db_path.mkdir(exist_ok=True)

# Cria o engine do SQLAlchemy com SQLite e configurações otimizadas
engine = create_async_engine(
    "sqlite+aiosqlite:///./data/app.db",
    poolclass=AsyncAdaptedQueuePool,
    pool_size=settings.SQLALCHEMY_POOL_SIZE,
    max_overflow=settings.SQLALCHEMY_MAX_OVERFLOW,
    pool_timeout=settings.SQLALCHEMY_POOL_TIMEOUT,
    pool_recycle=settings.SQLALCHEMY_POOL_RECYCLE,
    pool_pre_ping=settings.SQLALCHEMY_POOL_PRE_PING,
    connect_args={
        "check_same_thread": False,
        "timeout": 30
    },
    echo=settings.SQL_DEBUG
)

# Cria a fábrica de sessões com configurações otimizadas
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

def before_retry_callback(retry_state):
    """Callback executado antes de cada retry"""
    record_retry_attempt('sqlalchemy')
    logger.warning(
        f"Tentativa {retry_state.attempt_number} de conexão com o banco de dados"
    )

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.1, min=0.2, max=1),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    before=before_retry_callback,
    reraise=True
)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency para obter uma sessão do banco de dados com retry e métricas
    """
    with track_connection_time('sqlalchemy'):
        try:
            async with AsyncSessionLocal() as session:
                update_pool_metrics(engine)
                try:
                    record_retry_attempt('sqlalchemy', success=True)
                    yield session
                except Exception as e:
                    logger.error(f"Erro na sessão do banco de dados: {e}")
                    record_connection_error('sqlalchemy', type(e).__name__)
                    await session.rollback()
                    raise
                finally:
                    await session.close()
        except Exception as e:
            record_connection_error('sqlalchemy', type(e).__name__)
            raise

async def verify_database():
    """
    Verifica a conexão com o banco de dados com métricas detalhadas
    """
    with track_connection_time('health_check'):
        try:
            async with AsyncSessionLocal() as session:
                with track_query_time('health_check', 'ping'):
                    await session.execute("SELECT 1")
                
                update_pool_metrics(engine, 'health_check')
                logger.info("Conexão com banco de dados verificada com sucesso")
                return True
        except Exception as e:
            logger.error(f"Erro ao verificar conexão com banco de dados: {e}")
            record_connection_error('health_check', type(e).__name__)
            return False

__all__ = ["AsyncSessionLocal", "engine", "get_db", "verify_database"] 