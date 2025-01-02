from fastapi import APIRouter

router = APIRouter()

@router.get("/metrics")
async def get_metrics():
    """
    Endpoint para obter métricas da aplicação
    """
    return {
        "requests_total": 0,
        "requests_success": 0,
        "requests_error": 0,
        "response_time_avg": 0
    } 