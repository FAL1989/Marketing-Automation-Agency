from typing import Optional, Any, Dict, List
import hashlib
import json
import redis
from datetime import timedelta
import logging
from prometheus_client import Counter, Histogram
from ..core.optimizations import ROUTE_CACHE_CONFIG
from ..core.config import settings
from functools import lru_cache
import time
from threading import Lock

logger = logging.getLogger(__name__)

# Métricas para monitoramento do cache
CACHE_HITS = Counter(
    'cache_hits_total',
    'Total de hits no cache',
    ['route', 'source']  # Adicionado source para diferenciar Redis vs Local
)
CACHE_MISSES = Counter(
    'cache_misses_total',
    'Total de misses no cache',
    ['route', 'source']
)
CACHE_ERRORS = Counter(
    'cache_errors_total',
    'Total de erros no cache',
    ['type']
)
CACHE_OPERATION_DURATION = Histogram(
    'cache_operation_duration_seconds',
    'Duração das operações de cache',
    ['operation', 'source']
)

class LocalCache:
    """Cache local usando LRU"""
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
        self.lock = Lock()
        
    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key in self.cache:
                value, expiry = self.cache[key]
                if expiry > time.time():
                    return value
                del self.cache[key]
        return None
        
    def set(self, key: str, value: Any, ttl: int) -> None:
        with self.lock:
            # Limpa entradas expiradas
            now = time.time()
            expired = [k for k, (_, exp) in self.cache.items() if exp <= now]
            for k in expired:
                del self.cache[k]
                
            # Remove entradas antigas se necessário
            if len(self.cache) >= self.max_size:
                oldest = min(self.cache.items(), key=lambda x: x[1][1])
                del self.cache[oldest[0]]
                
            self.cache[key] = (value, now + ttl)

class CacheService:
    def __init__(self, redis_url: str = settings.REDIS_URL):
        self.redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=1.0,
            socket_connect_timeout=1.0,
            retry_on_timeout=True,
            retry_on_error=[redis.ConnectionError],
            max_connections=10,
            health_check_interval=30
        )
        self.default_ttl = timedelta(hours=1)
        self.local_cache = LocalCache()
        
    def _generate_key(self, route: str, params: Dict[str, Any]) -> str:
        """
        Gera uma chave única para o cache baseada na rota e parâmetros.
        Usa hash SHA-256 para garantir chaves consistentes e de tamanho fixo.
        """
        cache_data = {
            "route": route,
            "params": params
        }
        data_str = json.dumps(cache_data, sort_keys=True)
        return f"cache:{hashlib.sha256(data_str.encode()).hexdigest()}"
    
    async def get_cached_response(
        self,
        route: str,
        params: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Recupera uma resposta cacheada se disponível.
        Tenta primeiro o cache local, depois o Redis.
        """
        key = self._generate_key(route, params)
        
        # Tenta cache local primeiro
        with CACHE_OPERATION_DURATION.labels('get', 'local').time():
            local_value = self.local_cache.get(key)
            if local_value is not None:
                CACHE_HITS.labels(route=route, source='local').inc()
                logger.debug(f"Local cache hit para key: {key}")
                return local_value
            
            CACHE_MISSES.labels(route=route, source='local').inc()
        
        # Tenta Redis
        with CACHE_OPERATION_DURATION.labels('get', 'redis').time():
            try:
                cached = self.redis_client.get(key)
                
                if cached:
                    value = json.loads(cached)
                    # Atualiza cache local
                    route_config = ROUTE_CACHE_CONFIG.get(route, {})
                    ttl = route_config.get('ttl', self.default_ttl.seconds)
                    self.local_cache.set(key, value, ttl)
                    
                    CACHE_HITS.labels(route=route, source='redis').inc()
                    logger.debug(f"Redis cache hit para key: {key}")
                    return value
                
                CACHE_MISSES.labels(route=route, source='redis').inc()
                return None
                
            except Exception as e:
                CACHE_ERRORS.labels(type='get').inc()
                logger.error(f"Erro ao recuperar do Redis: {str(e)}")
                return None

    async def set_cached_response(
        self,
        route: str,
        params: Dict[str, Any],
        response: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Armazena uma resposta no cache.
        Atualiza tanto o cache local quanto o Redis.
        """
        key = self._generate_key(route, params)
        
        # Usa TTL da configuração da rota ou default
        if ttl is None:
            route_config = ROUTE_CACHE_CONFIG.get(route, {})
            ttl = route_config.get('ttl', self.default_ttl.seconds)
        
        # Atualiza cache local
        with CACHE_OPERATION_DURATION.labels('set', 'local').time():
            try:
                self.local_cache.set(key, response, ttl)
            except Exception as e:
                logger.error(f"Erro ao atualizar cache local: {str(e)}")
        
        # Atualiza Redis
        with CACHE_OPERATION_DURATION.labels('set', 'redis').time():
            try:
                serialized = json.dumps(response)
                self.redis_client.setex(key, ttl, serialized)
                logger.debug(f"Cache set para key: {key}, ttl: {ttl}")
                return True
                
            except Exception as e:
                CACHE_ERRORS.labels(type='set').inc()
                logger.error(f"Erro ao armazenar no Redis: {str(e)}")
                return False

    async def invalidate_cache(
        self,
        route: str,
        params: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Invalida entradas do cache.
        Limpa tanto o cache local quanto o Redis.
        """
        try:
            if params:
                # Invalida entrada específica
                key = self._generate_key(route, params)
                with self.local_cache.lock:
                    if key in self.local_cache.cache:
                        del self.local_cache.cache[key]
                self.redis_client.delete(key)
            else:
                # Invalida todas as entradas da rota
                pattern = f"cache:*{route}*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    # Limpa cache local
                    with self.local_cache.lock:
                        route_pattern = route.replace('/', '\\/')
                        self.local_cache.cache = {
                            k: v for k, v in self.local_cache.cache.items()
                            if route_pattern not in k
                        }
                    # Limpa Redis
                    self.redis_client.delete(*keys)
            
            logger.info(f"Cache invalidado para rota: {route}")
            return True
            
        except Exception as e:
            CACHE_ERRORS.labels(type='invalidate').inc()
            logger.error(f"Erro ao invalidar cache: {str(e)}")
            return False

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache.
        Inclui métricas tanto do cache local quanto do Redis.
        """
        stats = {
            "local_cache": {
                "size": len(self.local_cache.cache),
                "max_size": self.local_cache.max_size
            }
        }
        
        try:
            redis_info = self.redis_client.info()
            stats["redis"] = {
                "hits": redis_info.get("keyspace_hits", 0),
                "misses": redis_info.get("keyspace_misses", 0),
                "memory_used": redis_info.get("used_memory_human", "0B"),
                "total_keys": sum(
                    db.get("keys", 0)
                    for name, db in redis_info.items()
                    if name.startswith("db")
                ),
                "evicted_keys": redis_info.get("evicted_keys", 0),
                "expired_keys": redis_info.get("expired_keys", 0),
                "connected_clients": redis_info.get("connected_clients", 0)
            }
        except Exception as e:
            CACHE_ERRORS.labels(type='stats').inc()
            logger.error(f"Erro ao obter estatísticas do Redis: {str(e)}")
            stats["redis"] = {}
            
        return stats
    
    async def health_check(self) -> bool:
        """
        Verifica a saúde do cache.
        Considera saudável se pelo menos um dos caches (local ou Redis) estiver funcionando.
        """
        redis_healthy = False
        try:
            redis_healthy = bool(self.redis_client.ping())
        except Exception as e:
            logger.error(f"Erro no health check do Redis: {str(e)}")
        
        # Cache local sempre está disponível
        local_healthy = True
        
        return redis_healthy or local_healthy

cache_service = CacheService() 