from typing import Dict, Any, Optional
import json
import redis.asyncio as redis
from pydantic_settings import BaseSettings

class CacheSettings(BaseSettings):
    REDIS_URL: str
    CACHE_TTL: int = 3600  # 1 hora
    RATE_LIMIT_TTL: int = 60  # 1 minuto
    
    class Config:
        env_file = ".env"

settings = CacheSettings()

class CacheManager:
    def __init__(self):
        self.redis = None
    
    async def connect(self):
        """
        Estabelece conexão com o Redis
        """
        if not self.redis:
            self.redis = redis.from_url(settings.REDIS_URL)
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Recupera um valor do cache
        """
        if not self.redis:
            await self.connect()
            
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(
        self,
        key: str,
        value: Dict[str, Any],
        expire: Optional[int] = None
    ) -> None:
        """
        Armazena um valor no cache
        """
        if not self.redis:
            await self.connect()
            
        serialized = json.dumps(value)
        if expire is None:
            expire = settings.CACHE_TTL
        await self.redis.setex(key, expire, serialized)
    
    async def delete(self, key: str) -> None:
        """
        Remove um valor do cache
        """
        if not self.redis:
            await self.connect()
            
        await self.redis.delete(key)
    
    async def increment_rate_limit(
        self,
        key: str,
        amount: int = 1,
        ttl: Optional[int] = None
    ) -> int:
        """
        Incrementa um contador de rate limit
        Retorna o valor atual
        """
        if not self.redis:
            await self.connect()
            
        if ttl is None:
            ttl = settings.RATE_LIMIT_TTL
        
        tr = self.redis.pipeline()
        tr.incr(key, amount)
        tr.expire(key, ttl)
        result = await tr.execute()
        return result[0]
    
    async def get_rate_limit(self, key: str) -> int:
        """
        Obtém o valor atual do rate limit
        """
        if not self.redis:
            await self.connect()
            
        value = await self.redis.get(key)
        return int(value) if value else 0
    
    async def clear_rate_limit(self, key: str) -> None:
        """
        Limpa o rate limit
        """
        if not self.redis:
            await self.connect()
            
        await self.redis.delete(key)
    
    async def close(self):
        """
        Fecha a conexão com o Redis
        """
        if self.redis:
            await self.redis.close()
            self.redis = None

cache_manager = CacheManager() 