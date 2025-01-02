from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import asyncio
from functools import lru_cache
import logging
from prometheus_client import Histogram, Counter, Gauge

from ..core.optimizations import (
    optimization_settings,
    ROUTE_CACHE_CONFIG,
    ROUTE_RATE_LIMITS,
    PERFORMANCE_THRESHOLDS,
    BATCH_CONFIG,
    CIRCUIT_BREAKER_CONFIG
)
from ..services.cache_service import cache_service
from ..services.rate_limiter import TokenBucketRateLimiter
from ..monitoring.metrics import performance_metrics

logger = logging.getLogger(__name__)

# Métricas de performance
REQUEST_DURATION = Histogram(
    'request_duration_seconds',
    'Duração das requisições HTTP',
    ['method', 'route', 'status_code']
)

REQUEST_COUNT = Counter(
    'request_count_total',
    'Total de requisições HTTP',
    ['method', 'route', 'status_code']
)

ACTIVE_REQUESTS = Gauge(
    'active_requests',
    'Número de requisições ativas',
    ['method', 'route']
)

class OptimizationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.rate_limiter = TokenBucketRateLimiter()
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        route = request.url.path
        method = request.method
        
        # Incrementa contador de requisições ativas
        ACTIVE_REQUESTS.labels(method=method, route=route).inc()
        
        try:
            # Verifica rate limit
            if not await self._check_rate_limit(request):
                return Response(
                    content="Rate limit exceeded",
                    status_code=429
                )
            
            # Tenta obter do cache
            cached_response = await self._get_cached_response(request)
            if cached_response:
                return cached_response
            
            # Processa a requisição
            response = await self._process_request(request, call_next)
            
            # Armazena no cache se necessário
            await self._cache_response(request, response)
            
            # Registra métricas
            duration = time.time() - start_time
            self._record_metrics(method, route, response.status_code, duration)
            
            return response
            
        except Exception as e:
            logger.error(f"Erro no middleware de otimização: {str(e)}")
            return Response(
                content="Internal server error",
                status_code=500
            )
        finally:
            # Decrementa contador de requisições ativas
            ACTIVE_REQUESTS.labels(method=method, route=route).dec()
    
    async def _check_rate_limit(self, request: Request) -> bool:
        """Verifica se a requisição está dentro do rate limit"""
        route = request.url.path
        if route in ROUTE_RATE_LIMITS:
            config = ROUTE_RATE_LIMITS[route]
            client_id = request.client.host
            
            # Verifica rate limit
            allowed = await self.rate_limiter.check_rate_limit(
                key=f"rate_limit:{route}:{client_id}",
                max_requests=config["max_requests"],
                window=config["window"]
            )
            
            if not allowed:
                logger.warning(f"Rate limit excedido para {client_id} em {route}")
                return False
        
        return True
    
    async def _get_cached_response(self, request: Request) -> Optional[Response]:
        """Tenta obter resposta do cache"""
        route = request.url.path
        if route in ROUTE_CACHE_CONFIG:
            params = {
                "query": dict(request.query_params),
                "path": dict(request.path_params)
            }
            
            cached = await cache_service.get_cached_response(route, params)
            if cached:
                return Response(
                    content=cached["content"],
                    status_code=cached["status_code"],
                    headers=cached["headers"]
                )
        
        return None
    
    async def _process_request(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Processa a requisição"""
        response = await call_next(request)
        
        # Verifica performance thresholds
        route = request.url.path
        if route in PERFORMANCE_THRESHOLDS:
            thresholds = PERFORMANCE_THRESHOLDS[route]
            
            # Verifica tempo de resposta
            duration = time.time() - request.state.start_time
            if duration > thresholds["max_response_time"]:
                logger.warning(
                    f"Tempo de resposta alto em {route}: {duration:.2f}s"
                )
        
        return response
    
    async def _cache_response(self, request: Request, response: Response) -> None:
        """Armazena resposta no cache se necessário"""
        route = request.url.path
        if route in ROUTE_CACHE_CONFIG:
            config = ROUTE_CACHE_CONFIG[route]
            params = {
                "query": dict(request.query_params),
                "path": dict(request.path_params)
            }
            
            await cache_service.set_cached_response(
                route=route,
                params=params,
                response={
                    "content": response.body,
                    "status_code": response.status_code,
                    "headers": dict(response.headers)
                },
                ttl=config["ttl"]
            )
    
    def _record_metrics(
        self,
        method: str,
        route: str,
        status_code: int,
        duration: float
    ) -> None:
        """Registra métricas da requisição"""
        REQUEST_DURATION.labels(
            method=method,
            route=route,
            status_code=status_code
        ).observe(duration)
        
        REQUEST_COUNT.labels(
            method=method,
            route=route,
            status_code=status_code
        ).inc()

@lru_cache(maxsize=1000)
def get_route_config(route: str):
    """Cache de configurações por rota para evitar lookups repetidos"""
    return {
        "cache": ROUTE_CACHE_CONFIG.get(route, {}),
        "rate_limit": ROUTE_RATE_LIMITS.get(route, {}),
        "performance": PERFORMANCE_THRESHOLDS.get(route, {}),
        "batch": BATCH_CONFIG.get(route, {}),
        "circuit_breaker": CIRCUIT_BREAKER_CONFIG.get(route, CIRCUIT_BREAKER_CONFIG["default"])
    } 