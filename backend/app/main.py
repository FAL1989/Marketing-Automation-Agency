from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.routers import auth, content, templates, users, generations, test_endpoints, analytics
from app.api.routes import metrics
from app.core.security_middleware import SecurityMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.auth import AuthMiddleware
from app.dependencies import get_redis_client
from app.services.rate_limiter import TokenBucketRateLimiter
from .middleware.circuit_breaker import CircuitBreakerMiddleware
from .core.config import settings
import structlog
import redis.asyncio as redis
from typing import Optional
import time

logger = structlog.get_logger()

# Variáveis globais para serviços
redis_client: Optional[redis.Redis] = None
rate_limiter: Optional[TokenBucketRateLimiter] = None

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data: https:; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    global redis_client, rate_limiter
    
    # Inicializa serviços
    try:
        # Inicializa Redis
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=5,
            retry_on_timeout=True
        )
        await redis_client.ping()
        logger.info("Conexão com Redis estabelecida")
        
        # Inicializa Rate Limiter
        rate_limiter = TokenBucketRateLimiter(settings.REDIS_URL)
        logger.info("Rate Limiter inicializado")
        
    except Exception as e:
        logger.warning("Redis não disponível, continuando sem cache", error=str(e))
        redis_client = None
        rate_limiter = None
    
    yield
    
    # Cleanup
    try:
        if redis_client:
            await redis_client.close()
        if rate_limiter:
            await rate_limiter.close()
    except Exception as e:
        logger.error("Erro ao finalizar serviços", error=str(e))

# Cria a aplicação FastAPI
app = FastAPI(
    title="Backend API",
    description="API Backend com autenticação e rate limiting",
    version="1.0.0",
    lifespan=lifespan,
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "displayRequestDuration": True,
        "filter": True,
        "tryItOutEnabled": True
    }
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Middleware de segurança
app.add_middleware(SecurityHeadersMiddleware)

# Middleware de autenticação e rate limiting (opcional)
if rate_limiter:
    app.add_middleware(AuthMiddleware, rate_limiter=rate_limiter)

# Middleware de circuit breaker
app.add_middleware(
    CircuitBreakerMiddleware,
    endpoints_config={
        "/auth/login": {
            "failure_threshold": 5,
            "recovery_timeout": 30,
            "window_size": 100,
            "window_duration": 60
        }
    }
)

# Rotas da API
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(content.router, prefix="/content", tags=["content"])
app.include_router(templates.router, prefix="/templates", tags=["templates"])
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
app.include_router(generations.router, prefix="/generations", tags=["generations"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(test_endpoints.router, tags=["test"])

@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "message": "Backend API",
        "version": settings.VERSION,
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 