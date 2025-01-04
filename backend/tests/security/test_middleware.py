import pytest
from fastapi.testclient import TestClient
from ..conftest import test_client, test_user
from ...app.core.config import settings

def test_security_headers_middleware(test_client):
    """Testa o middleware de headers de segurança"""
    response = test_client.get("/")
    headers = response.headers
    
    # Verifica headers de segurança
    assert "content-security-policy" in headers
    assert "x-frame-options" in headers
    assert "x-content-type-options" in headers
    assert "x-xss-protection" in headers
    assert "referrer-policy" in headers

def test_rate_limit_middleware(test_client):
    """Testa o middleware de rate limiting"""
    # Faz múltiplas requisições
    responses = []
    for _ in range(settings.RATE_LIMIT_BURST + 1):
        responses.append(test_client.get("/"))
    
    # Verifica se alguma requisição foi limitada
    assert any(r.status_code == 429 for r in responses)
    
    # Verifica headers de rate limit
    last_response = responses[-1]
    assert "x-ratelimit-limit" in last_response.headers
    assert "x-ratelimit-remaining" in last_response.headers
    assert "x-ratelimit-reset" in last_response.headers

def test_cors_middleware(test_client):
    """Testa o middleware CORS"""
    # Requisição de origem permitida
    headers = {
        "Origin": settings.FRONTEND_URL,
        "Access-Control-Request-Method": "POST"
    }
    response = test_client.options("/", headers=headers)
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == settings.FRONTEND_URL
    
    # Requisição de origem não permitida
    headers = {
        "Origin": "http://malicious-site.com"
    }
    response = test_client.get("/", headers=headers)
    assert "access-control-allow-origin" not in response.headers

def test_auth_middleware(test_client, test_user):
    """Testa o middleware de autenticação"""
    # Rota protegida sem token
    response = test_client.get(f"{settings.API_V1_STR}/users/me")
    assert response.status_code == 401
    
    # Rota protegida com token inválido
    response = test_client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": "Bearer invalid"}
    )
    assert response.status_code == 401

def test_circuit_breaker_middleware(test_client):
    """Testa o middleware de circuit breaker"""
    # Configura o endpoint para teste
    endpoint = f"{settings.API_V1_STR}/auth/login"
    data = {"username": "wrong@example.com", "password": "wrong_password"}
    
    # Fase 1: Força falhas para ativar o circuit breaker
    responses = []
    for _ in range(settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD + 1):
        responses.append(
            test_client.post(endpoint, data=data)
        )
    
    # Verifica se o circuit breaker foi ativado
    assert any(r.status_code == 503 for r in responses), "Circuit breaker não foi ativado"
    
    # Fase 2: Verifica se o circuit breaker mantém o estado
    response = test_client.post(endpoint, data=data)
    assert response.status_code == 503, "Circuit breaker não manteve o estado"
    assert "retry_after" in response.json(), "Header Retry-After não presente"
    
    # Fase 3: Verifica informações do circuit breaker
    status = response.json()["circuit_breaker_status"]
    assert status["state"] == "open", "Estado do circuit breaker incorreto"
    assert status["failure_count"] >= settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD, "Contador de falhas incorreto"

def test_middleware_order(test_client, test_user):
    """Testa a ordem de execução dos middlewares"""
    # Faz uma requisição que ativa múltiplos middlewares
    response = test_client.post(
        f"{settings.API_V1_STR}/users/me",
        headers={
            "Origin": "http://malicious-site.com",
            "Authorization": "Bearer invalid"
        },
        json={"data": "test"}
    )
    
    # O middleware CORS deve bloquear antes do auth
    assert response.status_code == 403
    assert "cors" in response.json()["detail"].lower()

def test_error_handling_middleware(test_client):
    """Testa o middleware de tratamento de erros"""
    # Força um erro interno
    response = test_client.get("/force-error")
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "internal server error" in data["detail"].lower()

def test_logging_middleware(test_client):
    """Testa o middleware de logging"""
    # Faz uma requisição que deve ser logada
    response = test_client.get(
        "/",
        headers={"X-Request-ID": "test-request-id"}
    )
    assert response.status_code == 200
    assert "x-request-id" in response.headers 