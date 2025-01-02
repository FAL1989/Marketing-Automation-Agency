from fastapi import APIRouter, Request
from app.middleware.rate_limit import rate_limit

router = APIRouter(prefix="/api/v1", tags=["test"])

@router.get("/test-rate-limit")
@rate_limit(requests=100, window=60)  # 100 requests por minuto
async def test_rate_limit(request: Request):
    """Endpoint para testar o rate limiting"""
    return {"message": "Rate limit test successful", "client_ip": request.client.host} 