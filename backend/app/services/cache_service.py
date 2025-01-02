from typing import Optional, Any, Dict, List
import hashlib
import json
import redis
from datetime import timedelta
import logging
from prometheus_client import Counter, Histogram, Gauge
from ..core.optimizations import ROUTE_CACHE_CONFIG
from ..core.config import settings
from functools import lru_cache
import time
from threading import Lock
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)

# Métricas aprimoradas para monitoramento do cache
CACHE_HITS = Counter(
    'cache_hits_total',
    'Total de hits no cache',
    ['route', 'source', 'prediction']  # Adicionado prediction para monitorar cache preditivo
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
CACHE_SIZE = Gauge(
    'cache_size_bytes',
    'Tamanho atual do cache',
    ['source']
)
CACHE_PREDICTION_ACCURACY = Counter(
    'cache_prediction_accuracy_total',
    'Precisão das predições de cache',
    ['result']  # hit/miss
)

class PredictiveCache:
    """Cache preditivo que aprende padrões de acesso"""
    def __init__(self):
        self.access_patterns = defaultdict(int)
        self.route_patterns = defaultdict(lambda: defaultdict(int))
        self.last_access = {}
        self.lock = Lock()
        
    def record_access(self, route: str, params: Dict[str, Any]):
        """Registra um padrão de acesso para aprendizado"""
        with self.lock:
            key = json.dumps({"route": route, "params": params}, sort_keys=True)
            self.access_patterns[key] += 1
            
            # Registra padrões entre rotas
            if route in self.last_access:
                last_route = self.last_access[route]
                self.route_patterns[last_route][route] += 1
            
            self.last_access[route] = route
            
    def should_cache(self, route: str, params: Dict[str, Any]) -> bool:
        """Decide se um item deve ser cacheado baseado em padrões históricos"""
        key = json.dumps({"route": route, "params": params}, sort_keys=True)
        access_count = self.access_patterns.get(key, 0)
        
        # Se o item foi acessado mais de 3 vezes, vale a pena cachear
        return access_count >= 3
        
    def predict_next_routes(self, current_route: str, limit: int = 5) -> List[str]:
        """Prediz as próximas rotas prováveis baseado em padrões históricos"""
        if current_route not in self.route_patterns:
            return []
            
        patterns = self.route_patterns[current_route]
        return sorted(
            patterns.keys(),
            key=lambda x: patterns[x],
            reverse=True
        )[:limit]

class LocalCache:
    """Cache local otimizado usando LRU com priorização"""
    def __init__(self, max_size: int = 2000):  # Aumentado tamanho máximo
        self.cache = {}
        self.max_size = max_size
        self.lock = Lock()
        self.access_count = defaultdict(int)
        self.last_access_time = {}
        
    def _calculate_priority(self, key: str) -> float:
        """Calcula prioridade do item baseado em frequência e recência"""
        count = self.access_count[key]
        last_access = self.last_access_time.get(key, 0)
        time_factor = 1.0 / (time.time() - last_access + 1)
        return count * time_factor
        
    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key in self.cache:
                value, expiry = self.cache[key]
                if expiry > time.time():
                    # Atualiza estatísticas de acesso
                    self.access_count[key] += 1
                    self.last_access_time[key] = time.time()
                    return value
                del self.cache[key]
                del self.access_count[key]
                del self.last_access_time[key]
        return None
        
    def set(self, key: str, value: Any, ttl: int) -> None:
        with self.lock:
            # Limpa entradas expiradas
            now = time.time()
            expired = [k for k, (_, exp) in self.cache.items() if exp <= now]
            for k in expired:
                del self.cache[k]
                del self.access_count[k]
                del self.last_access_time[k]
                
            # Remove entradas com menor prioridade se necessário
            if len(self.cache) >= self.max_size:
                items = list(self.cache.keys())
                priorities = [(k, self._calculate_priority(k)) for k in items]
                lowest_priority = min(priorities, key=lambda x: x[1])[0]
                del self.cache[lowest_priority]
                del self.access_count[lowest_priority]
                del self.last_access_time[lowest_priority]
                
            self.cache[key] = (value, now + ttl)
            self.access_count[key] = 1
            self.last_access_time[key] = now
            
            # Atualiza métrica de tamanho
            try:
                size = len(json.dumps(self.cache).encode())
                CACHE_SIZE.labels(source='local').set(size)
            except:
                pass

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
        self.default_ttl = timedelta(hours=2)  # Aumentado TTL padrão
        self.local_cache = LocalCache()
        self.predictive_cache = PredictiveCache()
        self._prefetch_task = None
        
    async def _prefetch_predicted_routes(self, current_route: str):
        """Pré-carrega rotas previstas em background"""
        try:
            predicted_routes = self.predictive_cache.predict_next_routes(current_route)
            for route in predicted_routes:
                # Tenta carregar do Redis para o cache local
                pattern = f"cache:*{route}*"
                keys = self.redis_client.keys(pattern)
                for key in keys[:5]:  # Limita a 5 itens por rota
                    cached = self.redis_client.get(key)
                    if cached:
                        value = json.loads(cached)
                        self.local_cache.set(
                            key,
                            value,
                            self.default_ttl.seconds
                        )
        except Exception as e:
            logger.error(f"Erro no prefetch: {str(e)}")
            
    def _start_prefetch(self, route: str):
        """Inicia tarefa de prefetch em background"""
        if self._prefetch_task:
            self._prefetch_task.cancel()
        self._prefetch_task = asyncio.create_task(
            self._prefetch_predicted_routes(route)
        )

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
        Recupera uma resposta cacheada com suporte a predição.
        """
        key = self._generate_key(route, params)
        predicted = False
        
        # Registra acesso para aprendizado
        self.predictive_cache.record_access(route, params)
        
        # Tenta cache local primeiro
        with CACHE_OPERATION_DURATION.labels('get', 'local').time():
            local_value = self.local_cache.get(key)
            if local_value is not None:
                predicted = key in self.predictive_cache.access_patterns
                CACHE_HITS.labels(
                    route=route,
                    source='local',
                    prediction='true' if predicted else 'false'
                ).inc()
                if predicted:
                    CACHE_PREDICTION_ACCURACY.labels(result='hit').inc()
                logger.debug(f"Local cache hit para key: {key}")
                
                # Inicia prefetch em background
                self._start_prefetch(route)
                
                return local_value
            
            CACHE_MISSES.labels(route=route, source='local').inc()
            if predicted:
                CACHE_PREDICTION_ACCURACY.labels(result='miss').inc()
        
        # Tenta Redis
        with CACHE_OPERATION_DURATION.labels('get', 'redis').time():
            try:
                cached = self.redis_client.get(key)
                
                if cached:
                    value = json.loads(cached)
                    # Atualiza cache local se vale a pena cachear
                    if self.predictive_cache.should_cache(route, params):
                        route_config = ROUTE_CACHE_CONFIG.get(route, {})
                        ttl = route_config.get('ttl', self.default_ttl.seconds)
                        self.local_cache.set(key, value, ttl)
                    
                    CACHE_HITS.labels(
                        route=route,
                        source='redis',
                        prediction='false'
                    ).inc()
                    logger.debug(f"Redis cache hit para key: {key}")
                    
                    # Inicia prefetch em background
                    self._start_prefetch(route)
                    
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
        Armazena uma resposta no cache com suporte a predição.
        Atualiza tanto o cache local quanto o Redis.
        """
        key = self._generate_key(route, params)
        
        # Usa TTL da configuração da rota ou default
        if ttl is None:
            route_config = ROUTE_CACHE_CONFIG.get(route, {})
            ttl = route_config.get('ttl', self.default_ttl.seconds)
        
        # Só cacheia se valer a pena
        should_cache = self.predictive_cache.should_cache(route, params)
        
        # Atualiza cache local se necessário
        if should_cache:
            with CACHE_OPERATION_DURATION.labels('set', 'local').time():
                try:
                    self.local_cache.set(key, response, ttl)
                except Exception as e:
                    logger.error(f"Erro ao atualizar cache local: {str(e)}")
        
        # Atualiza Redis
        with CACHE_OPERATION_DURATION.labels('set', 'redis').time():
            try:
                serialized = json.dumps(response)
                
                # Usa pipeline para operações atômicas
                pipeline = self.redis_client.pipeline()
                pipeline.setex(key, ttl, serialized)
                
                # Atualiza metadados para análise
                meta_key = f"meta:{key}"
                metadata = {
                    "last_access": time.time(),
                    "access_count": 1,
                    "route": route,
                    "predicted": should_cache
                }
                pipeline.setex(meta_key, ttl, json.dumps(metadata))
                
                # Executa pipeline
                pipeline.execute()
                
                # Atualiza métrica de tamanho
                try:
                    size = len(serialized.encode())
                    CACHE_SIZE.labels(source='redis').set(size)
                except:
                    pass
                    
                logger.debug(f"Cache set para key: {key}, ttl: {ttl}, predicted: {should_cache}")
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
        Invalida entradas do cache com suporte a predição.
        Limpa tanto o cache local quanto o Redis.
        """
        try:
            if params:
                # Invalida entrada específica
                key = self._generate_key(route, params)
                with self.local_cache.lock:
                    if key in self.local_cache.cache:
                        del self.local_cache.cache[key]
                        del self.local_cache.access_count[key]
                        del self.local_cache.last_access_time[key]
                
                # Usa pipeline para operações atômicas
                pipeline = self.redis_client.pipeline()
                pipeline.delete(key)
                pipeline.delete(f"meta:{key}")
                pipeline.execute()
            else:
                # Invalida todas as entradas da rota
                pattern = f"cache:*{route}*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    # Limpa cache local
                    with self.local_cache.lock:
                        route_pattern = route.replace('/', '\\/')
                        to_delete = []
                        for k in self.local_cache.cache.keys():
                            if route_pattern in k:
                                to_delete.append(k)
                        for k in to_delete:
                            del self.local_cache.cache[k]
                            del self.local_cache.access_count[k]
                            del self.local_cache.last_access_time[k]
                    
                    # Limpa Redis usando pipeline
                    pipeline = self.redis_client.pipeline()
                    for key in keys:
                        pipeline.delete(key)
                        pipeline.delete(f"meta:{key}")
                    pipeline.execute()
            
            # Limpa predições relacionadas
            with self.predictive_cache.lock:
                self.predictive_cache.access_patterns = {
                    k: v for k, v in self.predictive_cache.access_patterns.items()
                    if route not in k
                }
                if route in self.predictive_cache.route_patterns:
                    del self.predictive_cache.route_patterns[route]
                for patterns in self.predictive_cache.route_patterns.values():
                    if route in patterns:
                        del patterns[route]
            
            logger.info(f"Cache invalidado para rota: {route}")
            return True
            
        except Exception as e:
            CACHE_ERRORS.labels(type='invalidate').inc()
            logger.error(f"Erro ao invalidar cache: {str(e)}")
            return False

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas detalhadas do cache.
        Inclui métricas tanto do cache local quanto do Redis.
        """
        stats = {
            "local_cache": {
                "size": len(self.local_cache.cache),
                "max_size": self.local_cache.max_size,
                "items_by_priority": {},
                "access_patterns": len(self.predictive_cache.access_patterns),
                "route_patterns": len(self.predictive_cache.route_patterns)
            }
        }
        
        # Calcula distribuição de prioridades
        priorities = {}
        for key in self.local_cache.cache:
            priority = self.local_cache._calculate_priority(key)
            priority_range = int(priority * 10)
            priorities[priority_range] = priorities.get(priority_range, 0) + 1
        stats["local_cache"]["items_by_priority"] = priorities
        
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
                "connected_clients": redis_info.get("connected_clients", 0),
                "used_memory_peak": redis_info.get("used_memory_peak_human", "0B"),
                "total_connections_received": redis_info.get("total_connections_received", 0),
                "instantaneous_ops_per_sec": redis_info.get("instantaneous_ops_per_sec", 0),
                "instantaneous_input_kbps": redis_info.get("instantaneous_input_kbps", 0),
                "instantaneous_output_kbps": redis_info.get("instantaneous_output_kbps", 0),
                "sync_full": redis_info.get("sync_full", 0),
                "sync_partial_ok": redis_info.get("sync_partial_ok", 0),
                "sync_partial_err": redis_info.get("sync_partial_err", 0)
            }
            
            # Adiciona métricas de predição
            prediction_stats = {
                "total_patterns": len(self.predictive_cache.access_patterns),
                "total_route_patterns": len(self.predictive_cache.route_patterns),
                "top_routes": sorted(
                    [
                        (route, len(patterns))
                        for route, patterns in self.predictive_cache.route_patterns.items()
                    ],
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
            }
            stats["prediction"] = prediction_stats
            
        except Exception as e:
            CACHE_ERRORS.labels(type='stats').inc()
            logger.error(f"Erro ao obter estatísticas do Redis: {str(e)}")
            stats["redis"] = {}
            
        return stats

    async def optimize_cache(self):
        """
        Otimiza o cache removendo entradas raramente acessadas e
        ajustando TTLs baseado em padrões de acesso.
        """
        try:
            # Analisa padrões de acesso
            access_patterns = self.predictive_cache.access_patterns
            route_patterns = self.predictive_cache.route_patterns
            
            # Remove padrões raramente acessados
            with self.predictive_cache.lock:
                self.predictive_cache.access_patterns = {
                    k: v for k, v in access_patterns.items()
                    if v >= 3  # Mantém apenas padrões frequentes
                }
                
                # Limpa padrões de rota antigos
                for route in list(route_patterns.keys()):
                    patterns = route_patterns[route]
                    # Remove rotas raramente relacionadas
                    patterns = {k: v for k, v in patterns.items() if v >= 2}
                    if patterns:
                        route_patterns[route] = patterns
                    else:
                        del route_patterns[route]
            
            # Otimiza TTLs no Redis
            for key in self.redis_client.scan_iter("cache:*"):
                try:
                    meta_key = f"meta:{key}"
                    meta_data = self.redis_client.get(meta_key)
                    if meta_data:
                        metadata = json.loads(meta_data)
                        access_count = metadata.get("access_count", 0)
                        last_access = metadata.get("last_access", 0)
                        
                        # Ajusta TTL baseado no uso
                        if access_count > 10 and time.time() - last_access < 3600:
                            # Aumenta TTL para itens frequentemente acessados
                            self.redis_client.expire(key, self.default_ttl.seconds * 2)
                        elif access_count < 2 and time.time() - last_access > 7200:
                            # Remove itens raramente acessados
                            self.redis_client.delete(key)
                            self.redis_client.delete(meta_key)
                except Exception as e:
                    logger.error(f"Erro ao otimizar key {key}: {str(e)}")
                    continue
            
            logger.info("Otimização do cache concluída com sucesso")
            return True
            
        except Exception as e:
            CACHE_ERRORS.labels(type='optimize').inc()
            logger.error(f"Erro ao otimizar cache: {str(e)}")
            return False

cache_service = CacheService() 