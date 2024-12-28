import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.app.middleware.rate_limit import RateLimitMiddleware
from backend.app.core.monitoring import setup_monitoring
import redis.asyncio as redis
from unittest.mock import AsyncMock, patch
from typing import Generator, Dict, Any

@pytest.fixture
def mock_redis() -> AsyncMock:
    mock = AsyncMock(spec=redis.Redis)
    mock.exists.return_value = False
    mock.incr.return_value = 1
    mock.expire.return_value = True
    mock.set.return_value = True
    return mock

@pytest.fixture
def custom_limits() -> Dict[str, tuple[int, int]]:
    return {
        "/test": (2, 60),  # 2 requests per minute
        "/api/v1": (5, 60)  # 5 requests per minute
    }

@pytest.fixture
def test_app(mock_redis: AsyncMock, custom_limits: Dict[str, tuple[int, int]]) -> TestClient:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, redis_client=mock_redis, limits=custom_limits)
    setup_monitoring(app)
    
    @app.get("/test")
    async def test_endpoint() -> dict:
        return {"message": "test"}
        
    @app.get("/api/v1")
    async def api_endpoint() -> dict:
        return {"message": "api"}
        
    return TestClient(app)

def test_basic_rate_limit(test_app: TestClient, mock_redis: AsyncMock) -> None:
    """Testa o rate limit básico"""
    # Primeira requisição (permitida)
    response = test_app.get("/test")
    assert response.status_code == 200
    
    # Segunda requisição (permitida)
    response = test_app.get("/test")
    assert response.status_code == 200
    
    # Simula excesso de requisições
    mock_redis.incr.return_value = 3
    response = test_app.get("/test")
    assert response.status_code == 429
    response_data = response.json()
    assert "detail" in response_data
    assert "too many requests" in response_data["detail"].lower()

def test_block_after_limit(test_app: TestClient, mock_redis: AsyncMock) -> None:
    """Testa bloqueio após exceder limite"""
    mock_redis.exists.return_value = True
    
    response = test_app.get("/test")
    assert response.status_code == 429
    response_data = response.json()
    assert "detail" in response_data
    assert "temporarily blocked" in response_data["detail"].lower()

@patch('backend.app.core.monitoring.log_rate_limit_event')
def test_rate_limit_monitoring(
    mock_log: AsyncMock,
    test_app: TestClient,
    mock_redis: AsyncMock
) -> None:
    """Testa integração com monitoramento"""
    # Força exceder limite
    mock_redis.incr.return_value = 61
    response = test_app.get("/test")
    
    assert response.status_code == 429
    mock_log.assert_called_once()
    
def test_different_paths(test_app: TestClient, mock_redis: AsyncMock) -> None:
    """Testa limites diferentes por path"""
    # Test path /test (limite 2)
    response = test_app.get("/test")
    assert response.status_code == 200
    
    mock_redis.incr.return_value = 3
    response = test_app.get("/test")
    assert response.status_code == 429
    
    # Test path /api/v1 (limite 5)
    mock_redis.incr.return_value = 1
    response = test_app.get("/api/v1")
    assert response.status_code == 200
    
    mock_redis.incr.return_value = 6
    response = test_app.get("/api/v1")
    assert response.status_code == 429

def test_redis_error_handling(test_app: TestClient, mock_redis: AsyncMock) -> None:
    """Testa tratamento de erros do Redis"""
    mock_redis.incr.side_effect = redis.RedisError("Connection error")
    
    response = test_app.get("/test")
    assert response.status_code == 200  # Fail open 