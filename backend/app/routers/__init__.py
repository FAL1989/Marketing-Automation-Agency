"""
Package de routers da aplicação.
"""

from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .metrics import router as metrics_router
from .monitoring import router as monitoring_router
from .agents import router as agents_router

__all__ = [
    "auth_router",
    "users_router",
    "metrics_router",
    "monitoring_router",
    "agents_router"
] 