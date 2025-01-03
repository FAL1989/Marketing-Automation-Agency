import functools
import hashlib
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Union
from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)

def cache_query(
    ttl: Optional[int] = None,
    dependencies: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    key_prefix: str = "query"
):
    """
    Decorador para cache de queries
    
    Args:
        ttl: Tempo de vida do cache em segundos
        dependencies: Lista de chaves das quais este cache depende
        tags: Lista de tags para agrupar caches relacionados
        key_prefix: Prefixo para a chave de cache
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(
            self,
            *args,
            cache_service: Optional[CacheService] = None,
            **kwargs
        ) -> Any:
            # Verifica se cache está disponível
            if not cache_service:
                return await func(self, *args, **kwargs)
                
            # Gera chave de cache
            key_parts = [
                key_prefix,
                func.__name__,
                hashlib.md5(
                    json.dumps(
                        {"args": args, "kwargs": kwargs},
                        sort_keys=True
                    ).encode()
                ).hexdigest()
            ]
            cache_key = ":".join(key_parts)
            
            # Tenta obter do cache
            cached = await cache_service.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit para query: {func.__name__}")
                return cached
                
            # Executa query
            result = await func(self, *args, **kwargs)
            
            # Armazena no cache
            await cache_service.set(
                cache_key,
                result,
                ttl=ttl,
                dependencies=dependencies,
                tags=tags
            )
            logger.debug(f"Cache miss para query: {func.__name__}")
            
            return result
            
        return wrapper
    return decorator

def invalidate_cache(
    keys: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    cascade: bool = True
):
    """
    Decorador para invalidar cache
    
    Args:
        keys: Lista de chaves para invalidar
        tags: Lista de tags para invalidar
        cascade: Se deve invalidar dependências em cascata
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(
            self,
            *args,
            cache_service: Optional[CacheService] = None,
            **kwargs
        ) -> Any:
            # Executa função
            result = await func(self, *args, **kwargs)
            
            # Verifica se cache está disponível
            if not cache_service:
                return result
                
            # Invalida chaves específicas
            if keys:
                for key in keys:
                    await cache_service.delete(key, cascade=cascade)
                    
            # Invalida por tags
            if tags:
                for tag in tags:
                    keys_to_invalidate = cache_service._tag_to_keys.get(tag, set())
                    for key in keys_to_invalidate:
                        await cache_service.delete(key, cascade=cascade)
                        
            return result
            
        return wrapper
    return decorator 