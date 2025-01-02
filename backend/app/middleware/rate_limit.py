from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
import time
import asyncio
from typing import Callable, Dict, Optional
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

def get_client_identifier(request: Request) -> str:
    """Obtém um identificador único para o cliente"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host
    
    client_id = request.headers.get("X-Client-ID", "anonymous")
    return f"{client_ip}:{client_id}"

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
            rate_key = f"rate_limit:{func.__name__}:{client_id}"
            
            # Verifica o número atual de requisições
            current = await redis_client.get(rate_key)
            if current is None:
                await redis_client.setex(rate_key, window, 1)
            else:
                current = int(current)
                if current >= requests:
                    raise HTTPException(
                        status_code=429,
                        detail="Too many requests"
                    )
                await redis_client.incr(rate_key)
            
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
        self.clients: Dict[str, Dict] = {}
    
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint
    ) -> Response:
        client_id = get_client_identifier(request)
        
        # Chave para o rate limiting global
        rate_key = f"global_rate:{client_id}"
        
        # Verifica o rate limit global
        current = await redis_client.get(rate_key)
        if current is None:
            await redis_client.setex(rate_key, 60, 1)
        else:
            current = int(current)
            if current >= self.requests_per_minute:
                raise HTTPException(
                    status_code=429,
                    detail="Global rate limit exceeded"
                )
            await redis_client.incr(rate_key)
        
        # Verifica o burst limit
        burst_key = f"burst:{client_id}"
        burst_count = await redis_client.get(burst_key)
        
        if burst_count is None:
            await redis_client.setex(burst_key, 1, 1)
        else:
            burst_count = int(burst_count)
            if burst_count >= self.burst_limit:
                raise HTTPException(
                    status_code=429,
                    detail="Burst limit exceeded"
                )
            await redis_client.incr(burst_key)
        
        response = await call_next(request)
        return response 