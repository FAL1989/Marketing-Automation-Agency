from typing import Optional, Dict, Tuple
import time
import logging
import structlog
import json
import asyncio
from ..core.config import settings
from ..core.redis import redis_manager
from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry
from prometheus_client.metrics import MetricWrapperBase
import math
from dataclasses import dataclass
from datetime import datetime

logger = structlog.get_logger()

# Cria um registro dedicado para métricas de rate limit
RATE_LIMIT_REGISTRY = CollectorRegistry()

# Registra métricas apenas se não existirem
def get_or_create_metric(metric_class, name, documentation, registry, **kwargs):
    try:
        return metric_class(name, documentation, registry=registry, **kwargs)
    except ValueError:
        # Se a métrica já existe, retorna a existente
        for metric in registry.collect():
            if metric.name == name:
                return next(
                    m for m in registry._names_to_collectors.values()
                    if isinstance(m, metric_class) and m._name == name
                )

# Métricas de rate limit
RATE_LIMIT_HITS = get_or_create_metric(
    Counter,
    "rate_limit_hits",
    "Total de requisições processadas pelo rate limiter",
    RATE_LIMIT_REGISTRY,
    labelnames=["route", "source"]
)

RATE_LIMIT_BLOCKED = get_or_create_metric(
    Counter,
    "rate_limit_blocked",
    "Total de requisições bloqueadas pelo rate limiter",
    RATE_LIMIT_REGISTRY,
    labelnames=["route", "source"]
)

RATE_LIMIT_CURRENT = get_or_create_metric(
    Gauge,
    "rate_limit_current",
    "Número atual de requisições no rate limiter",
    RATE_LIMIT_REGISTRY,
    labelnames=["route", "source"]
)

RATE_LIMIT_LATENCY = get_or_create_metric(
    Histogram,
    "rate_limit_latency",
    "Latência das operações do rate limiter",
    RATE_LIMIT_REGISTRY,
    labelnames=["source"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0)
)

@dataclass
class TokenBucket:
    """Representa um bucket do algoritmo de rate limiting"""
    tokens: float
    last_update: float
    rate: int
    burst: int

class TokenBucketRateLimiter:
    """Implementação de rate limiting usando Token Bucket com fallback local"""
    
    def __init__(self, redis_url: str):
        """
        Inicializa o rate limiter.
        
        Args:
            redis_url: URL do Redis (mantido para compatibilidade)
        """
        self._local_buckets: Dict[str, TokenBucket] = {}
        self._local_lock = asyncio.Lock()
        
        # Configurações padrão
        self.default_rate = settings.RATE_LIMIT_MAX_REQUESTS
        self.default_burst = settings.RATE_LIMIT_MAX_REQUESTS
        self.period = settings.RATE_LIMIT_PERIOD
        
        # Limites específicos por rota
        self.route_limits = {
            "/auth/login": {"rate": 30, "burst": 30},
            "/api/generate": {"rate": 50, "burst": 50},
            "/api/test": {"rate": settings.RATE_LIMIT_MAX_REQUESTS, "burst": settings.RATE_LIMIT_MAX_REQUESTS},
            "/api/v1/auth/mfa/verify": {"rate": 20, "burst": 20}  # Limite mais restritivo para MFA
        }
        
        # Limites por tipo de usuário
        self.user_type_limits = {
            "free": {"rate": settings.RATE_LIMIT_PER_MINUTE, "burst": settings.RATE_LIMIT_PER_MINUTE},
            "premium": {"rate": 300, "burst": 300},
            "enterprise": {"rate": 1000, "burst": 1000}
        }
    
    async def is_allowed(
        self,
        key: str,
        route: str,
        user_type: str = "free"
    ) -> Tuple[bool, Dict]:
        """
        Verifica se uma requisição está dentro do limite de taxa.
        
        Args:
            key: Chave única para identificar o cliente
            route: Rota da requisição
            user_type: Tipo do usuário (free, premium, enterprise)
            
        Returns:
            Tuple[bool, Dict]: (permitido, informações)
        """
        rate, burst = await self._get_bucket_config(route, user_type)
        
        try:
            with RATE_LIMIT_LATENCY.labels('redis').time():
                async with redis_manager.get_connection('rate_limit') as redis:
                    # Script Lua para rate limiting atômico
                    lua_script = """
                    local key = KEYS[1]
                    local rate = tonumber(ARGV[1])
                    local burst = tonumber(ARGV[2])
                    local now = tonumber(ARGV[3])
                    local period = tonumber(ARGV[4])
                    
                    local bucket = redis.call('hmget', key, 'tokens', 'last_update')
                    local tokens = tonumber(bucket[1] or burst)
                    local last_update = tonumber(bucket[2] or 0)
                    
                    -- Calcula tokens disponíveis
                    local elapsed = math.max(0, now - last_update)
                    tokens = math.min(burst, tokens + (elapsed * rate / period))
                    
                    -- Tenta consumir um token
                    local allowed = tokens >= 1
                    if allowed then
                        tokens = tokens - 1
                    end
                    
                    -- Atualiza o bucket
                    redis.call('hmset', key, 'tokens', tokens, 'last_update', now)
                    redis.call('expire', key, period)
                    
                    return {allowed and 1 or 0, tokens}
                    """
                    
                    now = time.time()
                    result = await redis.eval(
                        lua_script,
                        1,
                        key,
                        rate,
                        burst,
                        now,
                        self.period
                    )
                    
                    allowed = bool(result[0])
                    remaining = int(result[1])
                    
                    if allowed:
                        RATE_LIMIT_HITS.labels(route=route, source='redis').inc()
                    else:
                        RATE_LIMIT_BLOCKED.labels(route=route, source='redis').inc()
                    
                    RATE_LIMIT_CURRENT.labels(route=route, source='redis').set(remaining)
                    
                    return allowed, {
                        "remaining": remaining,
                        "limit": burst,
                        "reset": self.period
                    }
            
        except Exception as e:
            # Fallback para controle local
            logger.warning(f"Redis error, using local rate limit: {e}")
            with RATE_LIMIT_LATENCY.labels('local').time():
                allowed, remaining = await self._update_local_bucket(key, rate, burst)
                
                if allowed:
                    RATE_LIMIT_HITS.labels(route=route, source='local').inc()
                else:
                    RATE_LIMIT_BLOCKED.labels(route=route, source='local').inc()
                
                RATE_LIMIT_CURRENT.labels(route=route, source='local').set(remaining)
                
                return allowed, {
                    "remaining": remaining,
                    "limit": burst,
                    "reset": self.period
                }
    
    async def _get_bucket_config(self, route: str, user_type: str = "free") -> Tuple[int, int]:
        """Obtém configuração do bucket para uma rota e tipo de usuário"""
        if route in self.route_limits:
            return self.route_limits[route]["rate"], self.route_limits[route]["burst"]
        
        if user_type in self.user_type_limits:
            return self.user_type_limits[user_type]["rate"], self.user_type_limits[user_type]["burst"]
        
        return self.default_rate, self.default_burst
    
    async def _update_local_bucket(
        self,
        key: str,
        rate: int,
        burst: int
    ) -> Tuple[bool, int]:
        """Atualiza o bucket local"""
        async with self._local_lock:
            now = time.time()
            
            if key not in self._local_buckets:
                self._local_buckets[key] = TokenBucket(
                    tokens=burst,
                    last_update=now,
                    rate=rate,
                    burst=burst
                )
            
            bucket = self._local_buckets[key]
            
            # Atualiza tokens
            elapsed = now - bucket.last_update
            bucket.tokens = min(
                bucket.burst,
                bucket.tokens + (elapsed * bucket.rate / self.period)
            )
            bucket.last_update = now
            
            # Tenta consumir um token
            if bucket.tokens >= 1:
                bucket.tokens -= 1
                return True, int(bucket.tokens)
            
            return False, 0 