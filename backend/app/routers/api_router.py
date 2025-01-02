from fastapi import APIRouter
from . import auth, users, content, templates, analytics, test, health, metrics

api_router = APIRouter()

# Inclui todos os routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(content.router, prefix="/content", tags=["content"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(test.router, prefix="/test", tags=["test"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(metrics.router, tags=["metrics"]) 