from fastapi import APIRouter, HTTPException, status
import logging
import psutil
from ..core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/monitoring",
    tags=["monitoring"]
)

@router.get("/system")
async def get_system_metrics_endpoint():
    """
    Retorna métricas do sistema
    """
    logger.info("Iniciando coleta de métricas do sistema")
    try:
        metrics = {
            "cpu": {
                "percent": psutil.cpu_percent(interval=1)
            },
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "used": psutil.disk_usage('/').used,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            }
        }
        logger.info(f"Métricas coletadas com sucesso: {metrics}")
        return metrics
    except Exception as e:
        logger.error(f"Erro ao coletar métricas do sistema: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao coletar métricas do sistema: {str(e)}"
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