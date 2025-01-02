import pytest
from fastapi.testclient import TestClient
from ..conftest import test_client, test_user
from ...app.core.config import settings

def test_invalid_json(test_client):
    """Testa envio de JSON inválido"""
    response = test_client.post(
        f"{settings.API_V1_STR}/auth/login",
        data="invalid json",
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

def test_missing_required_field(test_client):
    """Testa envio de requisição sem campo obrigatório"""
    response = test_client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"username": "test"}  # Falta o campo password
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert any("password" in error["loc"] for error in data["detail"])

def test_invalid_field_type(test_client):
    """Testa envio de campo com tipo inválido"""
    response = test_client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={
            "username": 123,  # username deve ser string
            "password": "test"
        }
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert any("username" in error["loc"] for error in data["detail"])

def test_field_constraints(test_client):
    """Testa validação de restrições de campos"""
    # Testa senha muito curta
    response = test_client.post(
        f"{settings.API_V1_STR}/users/register",
        json={
            "email": "test@example.com",
            "password": "123",  # Senha muito curta
            "full_name": "Test User"
        }
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert any("password" in error["loc"] for error in data["detail"])
    
    # Testa email inválido
    response = test_client.post(
        f"{settings.API_V1_STR}/users/register",
        json={
            "email": "invalid-email",
            "password": "validpassword123",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert any("email" in error["loc"] for error in data["detail"])

def test_xss_prevention(test_client, test_user):
    """Testa prevenção contra XSS"""
    # Primeiro faz login
    login_response = test_client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={
            "username": settings.TEST_USER_EMAIL,
            "password": settings.TEST_USER_PASSWORD
        }
    )
    access_token = login_response.json()["access_token"]
    
    # Tenta enviar dados com XSS
    response = test_client.post(
        f"{settings.API_V1_STR}/users/profile",
        json={
            "name": "<script>alert('xss')</script>",
            "bio": "Normal text"
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code in [400, 422]
    data = response.json()
    assert "detail" in data

def test_sql_injection_prevention(test_client):
    """Testa prevenção contra SQL Injection"""
    response = test_client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={
            "username": "admin' OR '1'='1",
            "password": "anything"
        }
    )
    assert response.status_code == 401  # Não deve permitir login

def test_large_payload(test_client, test_user):
    """Testa envio de payload muito grande"""
    # Primeiro faz login
    login_response = test_client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={
            "username": settings.TEST_USER_EMAIL,
            "password": settings.TEST_USER_PASSWORD
        }
    )
    access_token = login_response.json()["access_token"]
    
    # Tenta enviar payload grande
    large_string = "a" * 1_000_000  # 1MB de dados
    response = test_client.post(
        f"{settings.API_V1_STR}/users/profile",
        json={"bio": large_string},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code in [400, 413]  # 413 Payload Too Large

def test_invalid_content_type(test_client):
    """Testa envio com Content-Type inválido"""
    response = test_client.post(
        f"{settings.API_V1_STR}/auth/login",
        data="username=test&password=test",
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 415  # Unsupported Media Type 