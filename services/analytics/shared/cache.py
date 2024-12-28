"""
Cache manager module
"""

from typing import Any, Optional
import redis.asyncio as redis
from app.core.config import settings

class CacheManager:
    """
    Gerenciador de cache usando Redis
    """
    
    def __init__(self):
        self.redis_client = None
    
    async def connect(self):
        """
        Estabelece conexão com Redis
        """
        if not self.redis_client:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
    
    async def close(self):
        """
        Fecha conexão com Redis
        """
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
    
    async def get_rate_limit(self, key: str) -> int:
        """
        Obtém valor do rate limit
        """
        if not self.redis_client:
            await self.connect()
        
        value = await self.redis_client.get(key)
        return int(value) if value else 0
    
    async def set_rate_limit(self, key: str, value: int, ttl: int = 3600):
        """
        Define valor do rate limit
        """
        if not self.redis_client:
            await self.connect()
        
        await self.redis_client.setex(key, ttl, value)
    
    async def increment_rate_limit(self, key: str, ttl: int = 3600) -> int:
        """
        Incrementa valor do rate limit
        """
        if not self.redis_client:
            await self.connect()
        
        value = await self.redis_client.incr(key)
        await self.redis_client.expire(key, ttl)
        return value

cache_manager = CacheManager() 