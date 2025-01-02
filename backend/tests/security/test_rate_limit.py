import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.middleware.rate_limit import RateLimitMiddleware
from app.core.config import settings
import redis
import time

@pytest.fixture
def redis_client():
    client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_RATELIMIT_DB,
        decode_responses=True
    )
    # Limpa o banco antes dos testes
    client.flushdb()
    return client

@pytest.fixture
def app():
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)
    
    @app.get("/test")
    def test_route():
        return {"message": "test"}
    
    @app.get("/metrics")
    def metrics_route():
        return {"metrics": "data"}
    
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_rate_limit_headers(client):
    """Testa se os headers de rate limit estão presentes"""
    response = client.get("/test")
    assert response.status_code == 200
    
    # Verifica headers de rate limit
    assert "X-Rate-Limit-Limit" in response.headers
    assert "X-Rate-Limit-Remaining" in response.headers
    assert "X-Rate-Limit-Reset" in response.headers
    
    # Verifica valores dos headers
    assert int(response.headers["X-Rate-Limit-Limit"]) == settings.RATE_LIMIT_PER_MINUTE
    assert int(response.headers["X-Rate-Limit-Remaining"]) == settings.RATE_LIMIT_PER_MINUTE - 1
    assert int(response.headers["X-Rate-Limit-Reset"]) == 60

def test_rate_limit_exceeded(client, redis_client):
    """Testa se o rate limit é aplicado corretamente"""
    # Faz requisições até atingir o limite
    for i in range(settings.RATE_LIMIT_PER_MINUTE):
        response = client.get("/test")
        assert response.status_code == 200
        remaining = int(response.headers["X-Rate-Limit-Remaining"])
        assert remaining == settings.RATE_LIMIT_PER_MINUTE - (i + 1)
    
    # Próxima requisição deve falhar
    response = client.get("/test")
    assert response.status_code == 429
    assert "Too many requests" in response.text

def test_rate_limit_excluded_paths(client):
    """Testa se os caminhos excluídos não são afetados pelo rate limit"""
    # Faz muitas requisições em um caminho excluído
    for _ in range(settings.RATE_LIMIT_PER_MINUTE + 10):
        response = client.get("/metrics")
        assert response.status_code == 200
        # Não deve ter headers de rate limit
        assert "X-Rate-Limit-Limit" not in response.headers

def test_rate_limit_different_paths(client):
    """Testa se o rate limit é aplicado separadamente para diferentes caminhos"""
    # Atinge o limite em um caminho
    for _ in range(settings.RATE_LIMIT_PER_MINUTE):
        response = client.get("/test")
        assert response.status_code == 200
    
    # Próxima requisição no mesmo caminho deve falhar
    response = client.get("/test")
    assert response.status_code == 429
    
    # Mas outro caminho deve funcionar
    response = client.get("/test2")
    assert response.status_code == 200

def test_rate_limit_reset(client, redis_client):
    """Testa se o rate limit é resetado após o período de janela"""
    # Faz algumas requisições
    for _ in range(5):
        response = client.get("/test")
        assert response.status_code == 200
    
    # Espera o tempo da janela
    time.sleep(60)
    
    # Deve poder fazer requisições novamente
    response = client.get("/test")
    assert response.status_code == 200
    assert int(response.headers["X-Rate-Limit-Remaining"]) == settings.RATE_LIMIT_PER_MINUTE - 1

def test_rate_limit_with_forwarded_ip(client):
    """Testa rate limit com IP forwarded"""
    headers = {"X-Forwarded-For": "1.2.3.4"}
    
    # Faz requisições até o limite
    for i in range(settings.RATE_LIMIT_PER_MINUTE):
        response = client.get("/test", headers=headers)
        assert response.status_code == 200
    
    # Próxima requisição deve falhar
    response = client.get("/test", headers=headers)
    assert response.status_code == 429
    
    # Mas deve funcionar com outro IP
    headers = {"X-Forwarded-For": "5.6.7.8"}
    response = client.get("/test", headers=headers)
    assert response.status_code == 200 