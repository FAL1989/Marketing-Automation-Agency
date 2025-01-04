from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.metrics import router as metrics_router
from app.api.v1.endpoints.monitoring import router as monitoring_router
from app.api.v1.endpoints.agents import router as agents_router

api_router = APIRouter()

api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["auth"]
)

api_router.include_router(
    users_router,
    prefix="/users",
    tags=["users"]
)

api_router.include_router(
    agents_router,
    tags=["agents"]
)

api_router.include_router(
    metrics_router,
    prefix="/metrics",
    tags=["metrics"]
)

api_router.include_router(
    monitoring_router,
    prefix="/monitoring",
    tags=["monitoring"]
)

@api_router.get("/health-check")
async def health_check():
    """
    Endpoint para verificação de saúde da API
    """
    return {"status": "healthy"} 