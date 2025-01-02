"""
Módulo principal da aplicação FastAPI
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .db.session import engine
from .db.base_class import Base
from .routers import api_router
from .middleware.security import SecurityMiddleware
from .middleware.rate_limit import RateLimitMiddleware

# Cria a aplicação FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
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