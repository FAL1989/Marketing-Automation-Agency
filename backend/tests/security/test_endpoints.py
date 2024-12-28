import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.user import User
from backend.app.core.security import create_access_token

client = TestClient(app)

def test_protected_endpoint_without_token():
    """Testa acesso a endpoint protegido sem token"""
    response = client.get("/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_protected_endpoint_with_invalid_token():
    """Testa acesso a endpoint protegido com token inválido"""
    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

def test_protected_endpoint_with_expired_token(test_user: User):
    """Testa acesso a endpoint protegido com token expirado"""
    from datetime import timedelta
    
    # Cria um token que já expirou
    token = create_access_token(
        data={"sub": test_user.email},
        expires_delta=timedelta(minutes=-1)
    )
    
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

def test_brute_force_protection(test_user: User):
    """Testa proteção contra força bruta no login"""
    # Tenta fazer login várias vezes com senha errada
    for _ in range(10):
        response = client.post(
            "/auth/login",
            data={
                "username": test_user.email,
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
    
    # Tenta fazer login com a senha correta
    response = client.post(
        "/auth/login",
        data={
            "username": test_user.email,
            "password": "testpassword"
        }
    )
    # Deve estar bloqueado após muitas tentativas
    assert response.status_code == 429
    assert "Too many failed attempts" in response.json()["detail"]

def test_sql_injection_protection(test_user: User):
    """Testa proteção contra SQL Injection"""
    # Tenta fazer login com SQL Injection
    response = client.post(
        "/auth/login",
        data={
            "username": "' OR '1'='1",
            "password": "' OR '1'='1"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciais inválidas"

def test_xss_protection():
    """Testa proteção contra XSS"""
    # Tenta enviar script malicioso
    script = "<script>alert('xss')</script>"
    response = client.post(
        "/auth/login",
        data={
            "username": script,
            "password": script
        }
    )
    assert response.status_code == 401
    # Verifica se o script não está presente na resposta
    assert script not in response.text 