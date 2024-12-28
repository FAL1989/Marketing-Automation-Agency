import pytest
from fastapi import FastAPI
import httpx
from backend.app.middleware.rate_limit import RateLimitMiddleware
import redis.asyncio as redis
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_redis():
    mock = MagicMock(spec=redis.Redis)
    mock.exists = AsyncMock(return_value=False)
    mock.incr = AsyncMock(return_value=1)
    mock.expire = AsyncMock(return_value=True)
    mock.set = AsyncMock(return_value=True)
    return mock

@pytest.fixture
def test_app(mock_redis):
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, redis_client=mock_redis)
    
    @app.get("/api/test")
    async def test_endpoint():
        return {"message": "test"}
        
    return app

@pytest.mark.asyncio
async def test_basic_rate_limit(test_app, mock_redis):
    """Testa o rate limit básico"""
    async with httpx.AsyncClient(app=test_app, base_url="http://test") as client:
        # Primeira requisição (permitida)
        mock_redis.incr.return_value = 1
        response = await client.get("/api/test")
        assert response.status_code == 200
        
        # Simula excesso de requisições
        mock_redis.incr.return_value = 61
        response = await client.get("/api/test")
        assert response.status_code == 429

@pytest.mark.asyncio
async def test_block_after_limit(test_app, mock_redis):
    """Testa bloqueio após exceder limite"""
    async with httpx.AsyncClient(app=test_app, base_url="http://test") as client:
        # Simula cliente bloqueado
        mock_redis.exists.return_value = True
        
        response = await client.get("/api/test")
        assert response.status_code == 429
        assert "too many requests" in response.json()["detail"].lower() 