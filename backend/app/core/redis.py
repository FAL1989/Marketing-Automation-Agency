"""
Cliente Redis
"""

import logging
from typing import Optional
import redis.asyncio as redis
from app.core.redis_config import get_redis_config, get_redis_url

logger = logging.getLogger(__name__)

# Conexão global do Redis
_redis: Optional[redis.Redis] = None

async def get_redis() -> redis.Redis:
    """
    Retorna conexão do Redis
    """
    global _redis
    
    if _redis is None:
        try:
            _redis = redis.from_url(
                get_redis_url(),
                **get_redis_config()
            )
            # Testa a conexão
            await _redis.ping()
            logger.info("Conexão com Redis estabelecida")
        except Exception as e:
            logger.error(f"Erro ao conectar ao Redis: {str(e)}")
            raise
            
    return _redis

async def close_redis():
    """
    Fecha conexão do Redis
    """
    global _redis
    
    if _redis is not None:
        await _redis.close()
        _redis = None
        logger.info("Conexão com Redis fechada") 