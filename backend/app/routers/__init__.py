"""
Package de routers da aplicação.
"""

from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .templates import router as templates_router
from .content import router as content_router
from .monitoring import router as monitoring_router
from .analytics import router as analytics_router
from .audit import router as audit_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(templates_router)
api_router.include_router(content_router)
api_router.include_router(monitoring_router)
api_router.include_router(analytics_router)
api_router.include_router(audit_router)

@api_router.get("/health-check")
async def health_check():
    """
    Endpoint para verificação de saúde da API
    """
    return {"status": "healthy"} 

auth = auth_router
users = users_router
templates = templates_router
content = content_router
monitoring = monitoring_router
analytics = analytics_router
audit = audit_router 