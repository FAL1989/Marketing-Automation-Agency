"""
Módulo principal da aplicação FastAPI
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from .core.config import settings
from .db.session import engine
from .db.base_class import Base
from .routers import api_router
from .middleware.security import SecurityMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .core.cache_optimizer import cache_optimizer
from .core.redis_config import configure_redis
from .services.cache_service import cache_service
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    # Startup
    logger.info("Iniciando serviços...")
    
    # Configura Redis
    logger.info("Configurando Redis...")
    redis_configured = await configure_redis(cache_service.redis_client)
    if not redis_configured:
        logger.warning("Falha ao configurar Redis. Usando configurações padrão.")
    
    # Inicia otimizador de cache
    await cache_optimizer.start()
    
    yield
    
    # Shutdown
    logger.info("Desligando serviços...")
    await cache_optimizer.stop()

# Cria a aplicação FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Configura o CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Middlewares
app.add_middleware(SecurityMiddleware)
app.add_middleware(RateLimitMiddleware)

# Routers
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup():
    """
    Cria as tabelas do banco de dados na inicialização
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("shutdown")
async def shutdown():
    """
    Fecha as conexões na finalização
    """
    await engine.dispose()

@app.get("/")
async def root():
    """
    Rota raiz da API
    """
    return {
        "message": "AI Agency API",
        "version": "1.0.0",
        "docs_url": f"{settings.API_V1_STR}/docs",
    } 