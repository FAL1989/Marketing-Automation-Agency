import pytest
from fastapi import status
from ..conftest import test_client, test_user
from ...app.core.config import settings

def test_rate_limit(test_client):
    """Testa o rate limiting nos endpoints"""
    # Faz múltiplas requisições rápidas
    responses = []
    for _ in range(10):
        responses.append(test_client.get("/"))
    
    # Verifica se alguma requisição foi limitada
    assert any(r.status_code == 429 for r in responses)
    
    # Verifica headers de rate limit
    last_response = responses[-1]
    assert "X-RateLimit-Limit" in last_response.headers
    assert "X-RateLimit-Remaining" in last_response.headers
    assert "X-RateLimit-Reset" in last_response.headers

def test_auth_endpoints(test_client, test_user):
    """Testa os endpoints de autenticação"""
    # Tenta login com credenciais inválidas
    response = test_client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={
            "username": "wrong@example.com",
            "password": "wrong_password"
        }
    )
    assert response.status_code == 401
    
    # Login com credenciais válidas
    response = test_client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={
            "username": settings.TEST_USER_EMAIL,
            "password": settings.TEST_USER_PASSWORD
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_protected_routes(test_client, test_user):
    """Testa as rotas protegidas"""
    # Tenta acessar rota protegida sem token
    response = test_client.get(f"{settings.API_V1_STR}/users/me")
    assert response.status_code == 401
    
    # Login para obter token
    login_response = test_client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={
            "username": settings.TEST_USER_EMAIL,
            "password": settings.TEST_USER_PASSWORD
        }
    )
    token = login_response.json()["access_token"]
    
    # Acessa rota protegida com token válido
    response = test_client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

def test_csrf_protection(test_client, test_user):
    """Testa a proteção CSRF"""
    # Login para obter token
    login_response = test_client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={
            "username": settings.TEST_USER_EMAIL,
            "password": settings.TEST_USER_PASSWORD
        }
    )
    token = login_response.json()["access_token"]
    
    # Tenta fazer uma requisição POST sem CSRF token
    response = test_client.post(
        f"{settings.API_V1_STR}/users/profile",
        json={"name": "Test"},
        headers={
            "Authorization": f"Bearer {token}",
            "Origin": "http://malicious-site.com"
        }
    )
    assert response.status_code == 403

def test_xss_protection(test_client, test_user):
    """Testa a proteção contra XSS"""
    # Login para obter token
    login_response = test_client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={
            "username": settings.TEST_USER_EMAIL,
            "password": settings.TEST_USER_PASSWORD
        }
    )
    token = login_response.json()["access_token"]
    
    # Tenta enviar dados com XSS
    response = test_client.post(
        f"{settings.API_V1_STR}/users/profile",
        json={"name": "<script>alert('xss')</script>"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code in [400, 422]

def test_sql_injection(test_client):
    """Testa proteção contra SQL injection"""
    response = test_client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={
            "username": "admin' OR '1'='1",
            "password": "anything"
        }
    )
    assert response.status_code == 401  # Não deve permitir login

# Nota: O teste do circuit breaker foi movido para test_middleware.py
# para consolidar todos os testes relacionados a middlewares em um único lugar 