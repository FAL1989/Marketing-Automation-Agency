from typing import Optional, Dict, Tuple
import time
from redis import asyncio as aioredis
import logging
from datetime import datetime, timedelta
import structlog
import json
import asyncio
from ..core.config import settings

logger = structlog.get_logger()

class RateLimiter:
    def __init__(self, redis_url: str):
        """
        Inicializa o rate limiter.
        
        Args:
            redis_url: URL de conexão com o Redis
        """
        self.redis = aioredis.from_url(redis_url)
        
    async def is_allowed(
        self,
        key: str,
        max_requests: int,
        time_window: int,
        cost: int = 1
    ) -> bool:
        """
        Verifica se uma requisição está dentro do limite.
        
        Args:
            key: Chave única para o limite (ex: "user:123" ou "ip:1.2.3.4")
            max_requests: Número máximo de requisições permitidas
            time_window: Janela de tempo em segundos
            cost: Custo da requisição em tokens
            
        Returns:
            bool: True se a requisição está dentro do limite
        """
        try:
            current_time = int(time.time())
            window_key = f"{key}:{current_time // time_window}"
            
            # Obtém o uso atual
            current_usage = await self.redis.get(window_key)
            current_usage = int(current_usage) if current_usage else 0
            
            # Verifica se excederia o limite
            if current_usage + cost > max_requests:
                return False
            
            # Incrementa o contador
            await self.redis.incrby(window_key, cost)
            
            # Define o tempo de expiração
            await self.redis.expire(
                window_key,
                time_window
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao verificar rate limit: {str(e)}")
            # Em caso de erro, permite a requisição
            return True
    
    async def get_remaining(
        self,
        key: str,
        max_requests: int,
        time_window: int
    ) -> int:
        """
        Retorna o número de requisições restantes.
        
        Args:
            key: Chave única para o limite
            max_requests: Número máximo de requisições permitidas
            time_window: Janela de tempo em segundos
            
        Returns:
            int: Número de requisições restantes
        """
        try:
            current_time = int(time.time())
            window_key = f"{key}:{current_time // time_window}"
            
            # Obtém o uso atual
            current_usage = await self.redis.get(window_key)
            current_usage = int(current_usage) if current_usage else 0
            
            return max(0, max_requests - current_usage)
            
        except Exception as e:
            logger.error(f"Erro ao obter requisições restantes: {str(e)}")
            return 0
    
    async def reset(self, key: str) -> None:
        """
        Reseta o contador para uma chave.
        
        Args:
            key: Chave a ser resetada
        """
        try:
            # Encontra todas as chaves do padrão
            pattern = f"{key}:*"
            keys = await self.redis.keys(pattern)
            
            if keys:
                await self.redis.delete(*keys)
                
        except Exception as e:
            logger.error(f"Erro ao resetar rate limit: {str(e)}")
    
    async def close(self) -> None:
        """Fecha a conexão com o Redis"""
        await self.redis.close()


class TokenBucketRateLimiter:
    """Implementação de rate limiting usando Token Bucket com fallback local"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._redis: Optional[aioredis.Redis] = None
        self._local_buckets: Dict[str, Dict] = {}
        self._local_lock = asyncio.Lock()
        
        # Configurações padrão
        self.default_rate = 100  # requisições por minuto
        self.default_burst = 50  # burst adicional
        self.window_size = 60  # segundos
        
        # Limites específicos por rota
        self.route_limits = {
            "/auth/login": {"rate": 30, "burst": 10},
            "/api/generate": {"rate": 50, "burst": 20},
            "/api/test": {"rate": 200, "burst": 100}
        }
        
        # Limites por tipo de usuário
        self.user_type_limits = {
            "free": {"rate": 60, "burst": 20},
            "premium": {"rate": 300, "burst": 100},
            "enterprise": {"rate": 1000, "burst": 500}
        }
    
    async def get_redis(self) -> Optional[aioredis.Redis]:
        """Obtém conexão Redis com retry"""
        if not self._redis:
            try:
                self._redis = aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_timeout=2,
                    retry_on_timeout=True
                )
                await self._redis.ping()
            except aioredis.ConnectionError as e:
                logger.error("Erro ao conectar ao Redis", error=str(e))
                self._redis = None
        return self._redis
    
    async def close(self):
        """Fecha a conexão Redis"""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    def _get_limits(self, route: str, user_type: str = "free") -> Tuple[int, int]:
        """Obtém limites específicos para rota e tipo de usuário"""
        route_config = self.route_limits.get(route, {})
        user_config = self.user_type_limits.get(user_type, {})
        
        rate = min(
            route_config.get("rate", self.default_rate),
            user_config.get("rate", self.default_rate)
        )
        burst = min(
            route_config.get("burst", self.default_burst),
            user_config.get("burst", self.default_burst)
        )
        
        return rate, burst
    
    async def _update_local_bucket(
        self,
        key: str,
        rate: int,
        burst: int
    ) -> Tuple[bool, int]:
        """Atualiza bucket local"""
        async with self._local_lock:
            now = datetime.utcnow().timestamp()
            bucket = self._local_buckets.get(key, {
                "tokens": burst,
                "last_update": now,
                "rate": rate,
                "burst": burst
            })
            
            # Calcula tokens disponíveis
            time_passed = now - bucket["last_update"]
            new_tokens = min(
                bucket["burst"],
                bucket["tokens"] + time_passed * (rate / 60.0)
            )
            
            if new_tokens >= 1:
                bucket["tokens"] = new_tokens - 1
                bucket["last_update"] = now
                self._local_buckets[key] = bucket
                return True, int(bucket["tokens"])
            return False, 0
    
    async def is_allowed(
        self,
        key: str,
        route: str,
        user_type: str = "free"
    ) -> Tuple[bool, Dict]:
        """Verifica se a requisição está dentro dos limites"""
        rate, burst = self._get_limits(route, user_type)
        redis_client = await self.get_redis()
        
        try:
            if redis_client:
                # Tenta usar Redis primeiro
                lua_script = """
                local key = KEYS[1]
                local rate = tonumber(ARGV[1])
                local burst = tonumber(ARGV[2])
                local now = tonumber(ARGV[3])
                local window = tonumber(ARGV[4])
                
                local bucket = redis.call('hgetall', key)
                if #bucket == 0 then
                    redis.call('hmset', key,
                        'tokens', burst - 1,
                        'last_update', now,
                        'rate', rate,
                        'burst', burst
                    )
                    redis.call('expire', key, window)
                    return {1, burst - 1}
                end
                
                local tokens = tonumber(bucket[2])
                local last_update = tonumber(bucket[4])
                local time_passed = now - last_update
                local new_tokens = math.min(
                    burst,
                    tokens + time_passed * (rate / 60.0)
                )
                
                if new_tokens >= 1 then
                    redis.call('hmset', key,
                        'tokens', new_tokens - 1,
                        'last_update', now
                    )
                    redis.call('expire', key, window)
                    return {1, math.floor(new_tokens - 1)}
                end
                
                return {0, 0}
                """
                
                now = datetime.utcnow().timestamp()
                result = await redis_client.eval(
                    lua_script,
                    1,
                    key,
                    rate,
                    burst,
                    now,
                    self.window_size
                )
                
                allowed = bool(result[0])
                remaining = int(result[1])
                
            else:
                # Fallback para controle local
                allowed, remaining = await self._update_local_bucket(key, rate, burst)
            
            response = {
                "allowed": allowed,
                "remaining": remaining,
                "limit": rate,
                "reset": int(now) + self.window_size
            }
            
            if not allowed:
                logger.warning(
                    "Rate limit excedido",
                    key=key,
                    route=route,
                    user_type=user_type,
                    remaining=remaining
                )
            
            return allowed, response
            
        except Exception as e:
            logger.error(
                "Erro no rate limiting",
                error=str(e),
                key=key,
                route=route
            )
            # Em caso de erro, permite a requisição mas registra
            return True, {
                "allowed": True,
                "remaining": 1,
                "limit": rate,
                "reset": int(datetime.utcnow().timestamp()) + self.window_size
            } 