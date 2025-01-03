from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
import time
import asyncio
from typing import Callable, Dict, Optional, Tuple
from functools import wraps
import redis.asyncio as redis
from app.core.config import settings

# Cliente Redis para rate limiting
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)

class TokenBucket:
    """Implementação do algoritmo Token Bucket"""
    
    def __init__(self, capacity: int, rate: float):
        """
        Args:
            capacity: Capacidade máxima do bucket
            rate: Taxa de preenchimento (tokens por segundo)
        """
        self.capacity = capacity
        self.rate = rate
        self.tokens = capacity
        self.last_update = time.time()
    
    def _refill(self) -> None:
        """Reabastece o bucket com tokens baseado no tempo decorrido"""
        now = time.time()
        delta = now - self.last_update
        self.tokens = min(
            self.capacity,
            self.tokens + delta * self.rate
        )
        self.last_update = now
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Tenta consumir tokens do bucket
        
        Args:
            tokens: Número de tokens a consumir
            
        Returns:
            bool: True se tokens foram consumidos, False caso contrário
        """
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

class TokenBucketRateLimiter:
    """Rate limiter usando Token Bucket com Redis"""
    
    def __init__(
        self,
        redis_client: redis.Redis,
        capacity: int,
        rate: float,
        key_prefix: str = "token_bucket"
    ):
        self.redis = redis_client
        self.capacity = capacity
        self.rate = rate
        self.key_prefix = key_prefix
    
    async def get_bucket_state(self, key: str) -> Tuple[float, float]:
        """
        Obtém o estado atual do bucket do Redis
        
        Returns:
            Tuple[float, float]: (tokens, last_update)
        """
        tokens_key = f"{self.key_prefix}:{key}:tokens"
        time_key = f"{self.key_prefix}:{key}:time"
        
        tokens = await self.redis.get(tokens_key)
        last_update = await self.redis.get(time_key)
        
        if tokens is None or last_update is None:
            return self.capacity, time.time()
            
        return float(tokens), float(last_update)
    
    async def update_bucket_state(
        self,
        key: str,
        tokens: float,
        last_update: float
    ) -> None:
        """Atualiza o estado do bucket no Redis"""
        tokens_key = f"{self.key_prefix}:{key}:tokens"
        time_key = f"{self.key_prefix}:{key}:time"
        
        pipe = self.redis.pipeline()
        pipe.set(tokens_key, tokens)
        pipe.set(time_key, last_update)
        await pipe.execute()
    
    async def consume(self, key: str, tokens: int = 1) -> bool:
        """
        Tenta consumir tokens para uma chave específica
        
        Args:
            key: Identificador único do cliente/recurso
            tokens: Número de tokens a consumir
            
        Returns:
            bool: True se tokens foram consumidos, False caso contrário
        """
        current_tokens, last_update = await self.get_bucket_state(key)
        
        # Calcula tokens disponíveis
        now = time.time()
        delta = now - last_update
        current_tokens = min(
            self.capacity,
            current_tokens + delta * self.rate
        )
        
        # Tenta consumir
        if current_tokens >= tokens:
            current_tokens -= tokens
            await self.update_bucket_state(key, current_tokens, now)
            return True
            
        return False

def get_client_identifier(request: Request) -> str:
    """Obtém um identificador único para o cliente"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host
    
    client_id = request.headers.get("X-Client-ID", "anonymous")
    return f"{client_ip}:{client_id}"

# Instância global do rate limiter
rate_limiter = TokenBucketRateLimiter(
    redis_client=redis_client,
    capacity=settings.RATE_LIMIT_REQUESTS,
    rate=settings.RATE_LIMIT_REQUESTS / settings.RATE_LIMIT_PERIOD,
    key_prefix="api_rate_limit"
)

def rate_limit(requests: int = 100, window: int = 60):
    """
    Decorator para aplicar rate limiting em endpoints específicos
    
    Args:
        requests: Número máximo de requisições permitidas
        window: Janela de tempo em segundos
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request") or args[0]
            client_id = get_client_identifier(request)
            
            # Chave única para o rate limiting deste endpoint
            rate_key = f"{func.__name__}:{client_id}"
            
            # Verifica o rate limit usando token bucket
            if not await rate_limiter.consume(rate_key):
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware global para rate limiting"""
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 1000,
        burst_limit: int = 50
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        
        # Rate limiter para controle global
        self.global_limiter = TokenBucketRateLimiter(
            redis_client=redis_client,
            capacity=requests_per_minute,
            rate=requests_per_minute / 60,
            key_prefix="global_rate_limit"
        )
        
        # Rate limiter para controle de burst
        self.burst_limiter = TokenBucketRateLimiter(
            redis_client=redis_client,
            capacity=burst_limit,
            rate=burst_limit / 1,  # 1 segundo
            key_prefix="burst_limit"
        )
    
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint
    ) -> Response:
        client_id = get_client_identifier(request)
        
        # Verifica o rate limit global
        if not await self.global_limiter.consume(client_id):
            raise HTTPException(
                status_code=429,
                detail="Global rate limit exceeded"
            )
        
        # Verifica o burst limit
        if not await self.burst_limiter.consume(client_id):
            raise HTTPException(
                status_code=429,
                detail="Burst limit exceeded"
            )
        
        response = await call_next(request)
        return response 