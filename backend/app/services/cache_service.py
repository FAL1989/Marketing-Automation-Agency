import logging
from typing import Any, Dict, List, Optional, Set, Union
from app.core.redis_config import get_redis
from app.core.cache_dependencies import dependency_manager

logger = logging.getLogger(__name__)

class CacheService:
    """
    Serviço para gerenciamento de cache com suporte a dependências e tags
    """
    def __init__(self):
        self._prefix = "cache:"

    def _get_full_key(self, key: str) -> str:
        """
        Retorna a chave completa com prefixo
        """
        return f"{self._prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """
        Obtém valor do cache
        """
        try:
            redis = await get_redis()
            full_key = self._get_full_key(key)
            value = await redis.get(full_key)
            
            if value is not None:
                logger.debug(f"Cache hit: {key}")
                return value
                
            logger.debug(f"Cache miss: {key}")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao obter cache: {str(e)}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        dependencies: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        Define valor no cache com suporte a dependências e tags
        """
        try:
            redis = await get_redis()
            full_key = self._get_full_key(key)
            
            # Define valor no Redis
            if ttl:
                await redis.setex(full_key, ttl, value)
            else:
                await redis.set(full_key, value)
                
            # Registra dependências
            if dependencies:
                dependency_manager.add_dependencies(key, dependencies)
                
            # Registra tags
            if tags:
                dependency_manager.add_tags(key, tags)
                
            logger.debug(f"Cache set: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao definir cache: {str(e)}")
            return False

    async def delete(self, key: str, cascade: bool = False) -> bool:
        """
        Remove valor do cache com suporte a invalidação em cascata
        """
        try:
            redis = await get_redis()
            full_key = self._get_full_key(key)
            
            # Obtém chaves dependentes
            keys_to_delete = {key}
            if cascade:
                keys_to_delete.update(dependency_manager.get_dependent_keys(key))
            
            # Remove valores do Redis
            full_keys = [self._get_full_key(k) for k in keys_to_delete]
            await redis.delete(*full_keys)
            
            # Remove dependências
            for k in keys_to_delete:
                dependency_manager.remove_key(k)
                
            logger.debug(f"Cache deleted: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao remover cache: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Verifica se chave existe no cache
        """
        try:
            redis = await get_redis()
            full_key = self._get_full_key(key)
            return await redis.exists(full_key)
        except Exception as e:
            logger.error(f"Erro ao verificar cache: {str(e)}")
            return False

    async def clear(self) -> bool:
        """
        Limpa todo o cache
        """
        try:
            redis = await get_redis()
            cursor = 0
            pattern = f"{self._prefix}*"
            
            while True:
                cursor, keys = await redis.scan(cursor, match=pattern)
                if keys:
                    await redis.delete(*keys)
                if cursor == 0:
                    break
                    
            # Limpa dependências
            dependency_manager.clear()
            
            logger.info("Cache limpo")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {str(e)}")
            return False

    async def get_stats(self) -> Dict[str, Union[int, float]]:
        """
        Retorna estatísticas do cache
        """
        try:
            redis = await get_redis()
            info = await redis.info()
            
            stats = {
                "hits": self.monitoring_service.get_metric("cache_hits"),
                "misses": self.monitoring_service.get_metric("cache_misses"),
                "memory_used": info.get("used_memory", 0),
                "total_connections": info.get("total_connections_received", 0),
                "expired_keys": info.get("expired_keys", 0)
            }
            
            if stats["hits"] + stats["misses"] > 0:
                stats["hit_ratio"] = stats["hits"] / (stats["hits"] + stats["misses"])
            else:
                stats["hit_ratio"] = 0
                
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {str(e)}")
            return {} 