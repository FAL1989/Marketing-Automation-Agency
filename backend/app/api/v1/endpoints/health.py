from fastapi import APIRouter, Response, status
from ....core.redis import check_redis_connection
from ....core.config import settings
from ....core.monitoring import get_system_metrics
import psutil
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Endpoint para verificar a saúde da aplicação.
    Verifica:
    - Conexão com Redis
    - Uso de CPU
    - Uso de memória
    - Espaço em disco
    """
    try:
        # Verifica a conexão com o Redis
        redis_ok = await check_redis_connection()
        
        # Coleta métricas do sistema
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Define o status geral
        system_healthy = (
            cpu_percent < 90 and  # CPU abaixo de 90%
            memory.percent < 90 and  # Memória abaixo de 90%
            disk.percent < 90  # Disco abaixo de 90%
        )
        
        status_value = "healthy" if (redis_ok and system_healthy) else "degraded"
        status_code = status.HTTP_200_OK if status_value == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
        
        response = {
            "status": status_value,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "services": {
                "redis": "up" if redis_ok else "down"
            },
            "metrics": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent
            }
        }
        
        return Response(
            content=str(response),
            status_code=status_code,
            media_type="application/json"
        )
        
    except Exception as e:
        logger.error(f"Erro no health check: {str(e)}")
        return Response(
            content=str({"status": "error", "detail": str(e)}),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            media_type="application/json"
        ) 