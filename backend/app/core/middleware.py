from typing import List
from fastapi import Request, HTTPException, status, FastAPI
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
import re
import structlog
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from .config import settings
import time
import logging
from typing import Optional
from prometheus_client import Counter, Histogram
from starlette.types import ASGIApp
from app.services.rate_limiter import TokenBucketRateLimiter
from app.core.monitoring import MonitoringService

logger = structlog.get_logger()

# Padrões suspeitos para detecção
SUSPICIOUS_PATTERNS = [
    r'UNION\s+SELECT',
    r'exec\s+xp_',
    r'\.\./etc/passwd',
    r'<script>.*?</script>',
    r'\.\./\.\.',
    r'%2e%2e%2f'
]

# Métricas Prometheus
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total de requisições HTTP",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Latência das requisições HTTP",
    ["method", "endpoint"]
)

class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Verificar padrões suspeitos na URL e headers
        url = str(request.url)
        headers = dict(request.headers)
        
        for pattern in SUSPICIOUS_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                logger.warning("suspicious_pattern_detected", 
                             pattern=pattern, 
                             url=url,
                             client_ip=request.client.host)
                raise HTTPException(status_code=403, detail="Suspicious pattern detected")
            
            for header_value in headers.values():
                if re.search(pattern, str(header_value), re.IGNORECASE):
                    logger.warning("suspicious_header_detected",
                                 pattern=pattern,
                                 header_value=header_value,
                                 client_ip=request.client.host)
                    raise HTTPException(status_code=403, detail="Suspicious pattern detected in headers")

        response = await call_next(request)
        
        # Adicionar headers de segurança
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

def setup_cors(app: FastAPI):
    """Configura o middleware CORS"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def setup_security_middleware(app: FastAPI):
    """Configura middlewares de segurança"""
    # Trusted Host Middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts_list,
    )
    app.add_middleware(SecurityMiddleware) 

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware para logging de requisições
    """
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.time()
        
        # Log da requisição
        logger.info(
            f"Requisição iniciada: {request.method} {request.url.path}"
        )
        
        try:
            response = await call_next(request)
            
            # Log da resposta
            process_time = time.time() - start_time
            logger.info(
                f"Requisição finalizada: {request.method} {request.url.path} "
                f"- Status: {response.status_code} - Tempo: {process_time:.2f}s"
            )
            
            return response
        except Exception as e:
            logger.error(
                f"Erro na requisição: {request.method} {request.url.path} - {str(e)}",
                exc_info=True
            )
            raise

class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware para coleta de métricas
    """
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.time()
        
        response = await call_next(request)
        
        # Registra métricas
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(time.time() - start_time)
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware para rate limiting usando TokenBucketRateLimiter
    """
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.monitoring = MonitoringService()
        self.rate_limiter = TokenBucketRateLimiter(
            monitoring_service=self.monitoring,
            max_requests=settings.RATE_LIMIT_REQUESTS,
            window_size=settings.RATE_LIMIT_PERIOD,
            burst_size=settings.RATE_LIMIT_BURST
        )
    
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint
    ) -> Response:
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        client_ip = request.client.host
        
        try:
            # Verifica rate limit
            allowed, headers = await self.rate_limiter.check_rate_limit(client_ip)
            
            if not allowed:
                logger.warning(f"Rate limit excedido para IP: {client_ip}")
                response = Response(
                    content="Rate limit excedido",
                    status_code=429
                )
                # Adiciona headers de rate limit
                for key, value in headers.items():
                    response.headers[key] = value
                return response
            
            # Executa a requisição
            response = await call_next(request)
            
            # Registra sucesso
            await self.rate_limiter.record_success(client_ip)
            
            # Adiciona headers de rate limit na resposta
            for key, value in headers.items():
                response.headers[key] = value
            
            return response
            
        except Exception as e:
            # Registra falha
            await self.rate_limiter.record_failure(client_ip, e)
            logger.error(f"Erro no rate limiting para IP {client_ip}: {str(e)}")
            raise