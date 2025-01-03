"""
Configuração do Redis
"""

from typing import Dict, Any, Optional
import redis.asyncio as redis
from app.core.config import settings

def get_redis_url() -> str:
    """
    Retorna a URL de conexão do Redis
    """
    return settings.REDIS_URL

def get_redis_config() -> Dict[str, Any]:
    """
    Retorna a configuração do Redis
    """
    return {
        "max_connections": settings.REDIS_POOL_SIZE,
        "socket_timeout": 5,
        "socket_connect_timeout": 5,
        "retry_on_timeout": True,
        "health_check_interval": 30,
        "auto_close_connection_pool": True
    }

# Cliente Redis global
_redis: Optional[redis.Redis] = None

async def get_redis() -> redis.Redis:
    """
    Retorna uma conexão Redis, inicializando se necessário
    """
    global _redis
    
    if _redis is None:
        _redis = redis.from_url(
            get_redis_url(),
            **get_redis_config(),
            decode_responses=True
        )
        # Testa a conexão
        await _redis.ping()
        
    return _redis

async def close_redis():
    """
    Fecha a conexão Redis
    """
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None 