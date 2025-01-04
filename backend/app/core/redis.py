"""
Cliente Redis
"""

from redis.asyncio import Redis, ConnectionPool
from redis import Redis as SyncRedis
from app.core.config import settings
import logging
import asyncio
from typing import Optional, Union

logger = logging.getLogger(__name__)

class RedisManager:
    _instance = None
    _pool = None
    _redis = None
    _sync_redis = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    async def _try_connect(cls) -> Optional[Redis]:
        """Tenta estabelecer uma conexão com o Redis com retry"""
        for attempt in range(settings.REDIS_RETRY_ATTEMPTS):
            try:
                cls._pool = ConnectionPool(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    max_connections=settings.REDIS_POOL_SIZE,
                    decode_responses=True,
                    retry_on_timeout=True,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0
                )
                redis = Redis(connection_pool=cls._pool)
                await redis.ping()
                logger.info("Conexão com Redis estabelecida com sucesso")
                return redis
            except Exception as e:
                logger.warning(f"Tentativa {attempt + 1} de conectar ao Redis falhou: {e}")
                if cls._pool:
                    await cls._pool.disconnect()
                    cls._pool = None
                if attempt < settings.REDIS_RETRY_ATTEMPTS - 1:
                    await asyncio.sleep(settings.REDIS_RETRY_DELAY)
                else:
                    logger.error("Todas as tentativas de conexão com Redis falharam")
                    raise

    @classmethod
    def _try_connect_sync(cls) -> Optional[SyncRedis]:
        """Tenta estabelecer uma conexão síncrona com o Redis"""
        try:
            redis = SyncRedis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0
            )
            redis.ping()
            logger.info("Conexão síncrona com Redis estabelecida com sucesso")
            return redis
        except Exception as e:
            logger.error(f"Erro ao conectar ao Redis de forma síncrona: {e}")
            raise

    @classmethod
    async def initialize(cls):
        """Inicializa a conexão com o Redis"""
        if cls._redis is None:
            cls._redis = await cls._try_connect()
        if settings.TESTING and cls._sync_redis is None:
            cls._sync_redis = cls._try_connect_sync()

    @classmethod
    async def get_redis(cls) -> Union[Redis, SyncRedis]:
        """Retorna uma conexão com o Redis"""
        if settings.TESTING:
            if cls._sync_redis is None:
                cls._sync_redis = cls._try_connect_sync()
            return cls._sync_redis
        else:
            if cls._redis is None:
                await cls.initialize()
            return cls._redis

    @classmethod
    async def close(cls):
        """Fecha a conexão com o Redis"""
        if cls._redis is not None:
            await cls._redis.aclose()
            cls._redis = None
        if cls._sync_redis is not None:
            cls._sync_redis.close()
            cls._sync_redis = None
        if cls._pool is not None:
            await cls._pool.disconnect()
            cls._pool = None
            logger.info("Conexão com Redis fechada")

redis_manager = RedisManager()

async def get_redis() -> Union[Redis, SyncRedis]:
    """Helper function para obter uma conexão com o Redis"""
    return await redis_manager.get_redis() 