from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

router = APIRouter()

@router.get("/metrics")
async def get_metrics():
    """
    Endpoint para obter métricas da aplicação no formato Prometheus
    """
    return PlainTextResponse(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    ) 