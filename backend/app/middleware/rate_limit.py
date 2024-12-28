from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
import time
import logging
from redis import Redis
from typing import Optional, Any
from app.core.monitoring import log_rate_limit_event

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, redis_client: Optional[Redis] = None, requests_per_minute: int = 60):
        super().__init__(app)
        self.redis_client = redis_client
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 1 minuto em segundos

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self.redis_client:
            return await call_next(request)

        # Obtém o IP do cliente
        client_ip = request.client.host if request.client else "unknown"
        
        # Chave única para o cliente no Redis
        key = f"rate_limit:{client_ip}"
        
        # Obtém o timestamp atual
        current_time = int(time.time())
        
        try:
            # Limpa registros antigos e adiciona o novo
            pipeline = self.redis_client.pipeline()
            pipeline.zremrangebyscore(key, 0, current_time - self.window_size)
            pipeline.zadd(key, {str(current_time): current_time})
            pipeline.zcard(key)
            pipeline.expire(key, self.window_size)
            _, _, request_count, _ = pipeline.execute()
            
            # Verifica se excedeu o limite
            if request_count > self.requests_per_minute:
                # Registra o evento de rate limit
                await log_rate_limit_event(client_ip)
                
                # Retorna erro 429 (Too Many Requests)
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please try again later."
                )
            
            # Processa a requisição normalmente
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(f"Error in rate limit middleware: {str(e)}")
            # Em caso de erro no Redis, permite a requisição
            return await call_next(request) 