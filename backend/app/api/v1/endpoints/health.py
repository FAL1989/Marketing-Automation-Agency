from fastapi import APIRouter, Response
from ....core.redis import check_redis_connection

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Endpoint para verificar a saúde da aplicação
    """
    # Verifica a conexão com o Redis
    redis_ok = await check_redis_connection()
    
    status = "healthy" if redis_ok else "degraded"
    
    return {
        "status": status,
        "services": {
            "redis": "up" if redis_ok else "down"
        }
    } 