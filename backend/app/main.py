"""
Módulo principal da aplicação FastAPI
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from prometheus_client import make_asgi_app
from starlette.middleware.base import BaseHTTPMiddleware
from .core.config import settings
from .db.session import engine
from .db.base_all import Base
from .routers import api_router
from .middleware.security import SecurityMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.metrics import metrics_middleware
from contextlib import asynccontextmanager

# Importa todos os modelos para que o SQLAlchemy os conheça
from .models.user import User  # noqa
from .models.audit import AuditLog  # noqa
from .models.content import Content  # noqa
from .models.template import Template  # noqa
from .models.generation import Generation  # noqa

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    # Startup
    logger.info("Iniciando serviços...")
    # Cria as tabelas do banco de dados
    async with engine.begin() as conn:
        logger.info("Criando tabelas do banco de dados...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Tabelas criadas com sucesso!")
    yield
    # Shutdown
    logger.info("Desligando serviços...")
    await engine.dispose()

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
app.middleware("http")(metrics_middleware)

# Routers
app.include_router(api_router, prefix=settings.API_V1_STR)

# Endpoint Prometheus - ajustado para evitar redirecionamento
metrics_app = make_asgi_app()
app.mount("/metrics/", metrics_app, name="metrics")

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