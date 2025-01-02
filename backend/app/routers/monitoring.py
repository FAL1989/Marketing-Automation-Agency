from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict
from ..dependencies import get_current_user, get_db
from ..models.user import User
from ..core.monitoring import get_system_metrics, get_application_metrics
from ..core.config import settings

router = APIRouter(
    prefix="/monitoring",
    tags=["monitoring"]
)

@router.get("/metrics")
async def get_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retorna métricas do sistema e da aplicação
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem acessar as métricas"
        )
    
    try:
        system_metrics = await get_system_metrics()
        app_metrics = await get_application_metrics(db)
        
        return {
            "system": system_metrics,
            "application": app_metrics
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao coletar métricas: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """
    Endpoint de health check
    """
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    } 