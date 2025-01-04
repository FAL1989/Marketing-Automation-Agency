"""
Módulo principal da aplicação FastAPI
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.core.middleware import (
    LoggingMiddleware,
    MetricsMiddleware,
    RateLimitMiddleware
)
from app.middleware.circuit_breaker import CircuitBreakerMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração do Circuit Breaker
circuit_breaker_config = {
    f"{settings.API_V1_STR}/protected/resource": {
        "service_name": "protected_resource",
        "failure_threshold": settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
        "reset_timeout": settings.CIRCUIT_BREAKER_RESET_TIMEOUT,
        "half_open_timeout": 5
    }
}

# Middlewares
app.add_middleware(LoggingMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(CircuitBreakerMiddleware, endpoints_config=circuit_breaker_config)

# Rotas
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    """
    Endpoint para verificação de saúde da aplicação
    """
    return {"status": "ok"} 