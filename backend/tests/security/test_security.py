import pytest
from fastapi import status
from ..conftest import test_client, test_user
from ...app.core.config import settings
from ...app.core.security import SecurityService

def test_security_headers(test_client):
    """Testa os headers de segurança"""
    response = test_client.get("/")
    
    # Verifica headers obrigatórios
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert "Content-Security-Policy" in response.headers
    assert "Strict-Transport-Security" in response.headers
    assert "Referrer-Policy" in response.headers

def test_cors_configuration(test_client):
    """Testa a configuração CORS"""
    # Origem permitida
    headers = {
        "Origin": settings.FRONTEND_URL,
        "Access-Control-Request-Method": "POST"
    }
    response = test_client.options("/", headers=headers)
    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == settings.FRONTEND_URL
    
    # Origem não permitida
    headers["Origin"] = "http://malicious-site.com"
    response = test_client.options("/", headers=headers)
    assert response.status_code == 400

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
    
    # Requisição sem CSRF token
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
    """Testa a proteção contra SQL Injection"""
    response = test_client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={
            "username": "admin' OR '1'='1",
            "password": "anything"
        }
    )
    assert response.status_code == 401

def test_rate_limit(test_client):
    """Testa o rate limiting"""
    # Faz múltiplas requisições
    responses = []
    for _ in range(settings.RATE_LIMIT_PER_SECOND + 1):
        responses.append(test_client.get("/"))
    
    # Verifica se alguma requisição foi limitada
    assert any(r.status_code == 429 for r in responses)

def test_jwt_security(test_client, test_user):
    """Testa a segurança do JWT"""
    # Login para obter token
    login_response = test_client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={
            "username": settings.TEST_USER_EMAIL,
            "password": settings.TEST_USER_PASSWORD
        }
    )
    token = login_response.json()["access_token"]
    
    # Tenta acessar rota protegida sem token
    response = test_client.get(f"{settings.API_V1_STR}/users/me")
    assert response.status_code == 401
    
    # Acessa com token válido
    response = test_client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    # Tenta com token inválido
    response = test_client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401

def test_password_hashing():
    """Testa o hashing de senhas"""
    service = SecurityService()
    password = "test_password"
    
    # Gera hash
    hashed = service.get_password_hash(password)
    assert hashed != password
    
    # Verifica hash
    assert service.verify_password(password, hashed)
    assert not service.verify_password("wrong_password", hashed)

def test_token_generation():
    """Testa a geração de tokens"""
    service = SecurityService()
    
    # Gera token de acesso
    access_token = service.create_access_token(
        data={"sub": "test@example.com"}
    )
    assert access_token
    
    # Gera token de refresh
    refresh_token = service.create_refresh_token(
        data={"sub": "test@example.com"}
    )
    assert refresh_token
    
    # Verifica tokens diferentes
    assert access_token != refresh_token 