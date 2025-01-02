import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from ...app.middleware.rate_limit import RateLimitMiddleware
from ...app.monitoring.security_metrics import SecurityMetrics
from ...app.core.config import settings
from unittest.mock import Mock, patch
import time

@pytest.fixture
def app():
    """
    Fixture que cria uma aplicação FastAPI com o RateLimitMiddleware
    """
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    @app.get("/excluded")
    async def excluded_endpoint():
        return {"message": "excluded"}
    
    return app

@pytest.fixture
def client(app):
    """
    Fixture que cria um cliente de teste
    """
    return TestClient(app)

@pytest.fixture
def mock_redis():
    """
    Fixture que cria um mock do Redis
    """
    with patch("app.core.redis.redis_client") as mock:
        yield mock

def test_rate_limit_headers(client):
    """
    Testa se os headers de rate limit estão sendo adicionados corretamente
    """
    response = client.get("/test")
    assert response.status_code == 200
    
    # Verifica headers de rate limit
    assert "X-Rate-Limit-Limit" in response.headers
    assert "X-Rate-Limit-Remaining" in response.headers
    assert "X-Rate-Limit-Reset" in response.headers
    
    # Verifica valores dos headers
    assert int(response.headers["X-Rate-Limit-Limit"]) == settings.RATE_LIMIT_PER_MINUTE
    assert int(response.headers["X-Rate-Limit-Remaining"]) >= 0
    assert int(response.headers["X-Rate-Limit-Reset"]) >= 0

@patch("app.core.redis.redis_client.incr")
@patch("app.core.redis.redis_client.expire")
@patch("app.core.redis.redis_client.ttl")
def test_rate_limit_enforcement(mock_ttl, mock_expire, mock_incr, client):
    """
    Testa se o rate limit está sendo aplicado corretamente
    """
    # Configura os mocks
    mock_incr.return_value = 1
    mock_ttl.return_value = 60
    
    # Primeira requisição (dentro do limite)
    response = client.get("/test")
    assert response.status_code == 200
    mock_incr.assert_called_once()
    mock_expire.assert_called_once()
    
    # Reseta os mocks
    mock_incr.reset_mock()
    mock_expire.reset_mock()
    mock_incr.return_value = settings.RATE_LIMIT_PER_MINUTE + 1
    
    # Requisição que excede o limite
    with pytest.raises(HTTPException) as exc_info:
        response = client.get("/test")
    assert exc_info.value.status_code == 429
    mock_incr.assert_called_once()
    mock_expire.assert_not_called()

def test_excluded_paths(client):
    """
    Testa se os caminhos excluídos não estão sujeitos ao rate limit
    """
    # Adiciona o caminho aos excluídos
    settings.RATE_LIMIT_EXCLUDE_PATHS.append("/excluded")
    
    # Faz várias requisições ao endpoint excluído
    for _ in range(settings.RATE_LIMIT_PER_MINUTE + 1):
        response = client.get("/excluded")
        assert response.status_code == 200

@patch.object(SecurityMetrics, "record_rate_limit_violation")
def test_rate_limit_violation_recording(mock_record_violation, client, mock_redis):
    """
    Testa se as violações de rate limit estão sendo registradas
    """
    # Configura o mock do Redis para simular limite excedido
    mock_redis.incr.return_value = settings.RATE_LIMIT_PER_MINUTE + 1
    mock_redis.ttl.return_value = 60
    
    # Faz uma requisição que excede o limite
    with pytest.raises(HTTPException) as exc_info:
        response = client.get("/test")
    assert exc_info.value.status_code == 429
    
    # Verifica se a violação foi registrada
    mock_record_violation.assert_called_once()
    args = mock_record_violation.call_args[1]
    assert args["path"] == "/test"
    assert "ip" in args

@patch.object(SecurityMetrics, "record_request_latency")
def test_request_latency_recording(mock_record_latency, client):
    """
    Testa se a latência das requisições está sendo registrada
    """
    response = client.get("/test")
    assert response.status_code == 200
    mock_record_latency.assert_called_once()
    
    # Verifica os argumentos da chamada
    args = mock_record_latency.call_args[1]
    assert "path" in args
    assert "method" in args
    assert "start_time" in args
    assert args["path"] == "/test"
    assert args["method"] == "GET"

def test_client_identifier(client):
    """
    Testa a geração de identificadores únicos para clientes
    """
    # Faz requisições com diferentes IPs
    headers1 = {"X-Forwarded-For": "1.1.1.1"}
    headers2 = {"X-Forwarded-For": "2.2.2.2"}
    
    response1 = client.get("/test", headers=headers1)
    response2 = client.get("/test", headers=headers2)
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # As requisições devem ter diferentes identificadores no Redis
    # Isso é verificado indiretamente através dos headers
    assert response1.headers["X-Rate-Limit-Remaining"] == response2.headers["X-Rate-Limit-Remaining"] 