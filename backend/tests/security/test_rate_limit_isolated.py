import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from ..conftest import test_client, test_user
from ...app.core.config import settings
from ...app.middleware.rate_limit import RateLimitMiddleware

def create_test_app():
    """Cria uma aplicação FastAPI isolada para testes"""
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)
    
    @app.get("/api/test")
    async def test_endpoint():
        return {"message": "test"}
    
    return app

@pytest.fixture
def isolated_client():
    """Fixture que retorna um cliente de teste com uma aplicação isolada"""
    app = create_test_app()
    return TestClient(app)

def test_basic_rate_limit(isolated_client):
    """Testa o rate limiting básico em uma aplicação isolada"""
    # Faz múltiplas requisições rápidas
    for _ in range(settings.RATE_LIMIT_BURST):
        response = isolated_client.get("/api/test")
        assert response.status_code == 200
    
    # A próxima requisição deve ser limitada
    response = isolated_client.get("/api/test")
    assert response.status_code == 429

def test_block_after_limit(isolated_client):
    """Testa o bloqueio após exceder o limite"""
    # Excede o limite
    for _ in range(settings.RATE_LIMIT_BURST + 1):
        isolated_client.get("/api/test")
    
    # Tenta fazer mais uma requisição
    response = isolated_client.get("/api/test")
    assert response.status_code == 429
    
    # Verifica a mensagem de erro
    data = response.json()
    assert "detail" in data
    assert "rate limit exceeded" in data["detail"].lower() 