import pytest
from fastapi.testclient import TestClient
from backend.app.main import create_app
from backend.app.core import monitoring

@pytest.fixture
def test_client(mock_redis):
    """Cria um cliente de teste com Redis mockado"""
    app = create_app()
    return TestClient(app)

def test_login_success(test_client):
    """Testa login com sucesso"""
    response = test_client.post(
        "/auth/login",
        data={
            "username": "test_user",
            "password": "correct_password"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()

def test_login_wrong_password(test_client):
    """Testa login com senha incorreta"""
    response = test_client.post(
        "/auth/login",
        data={
            "username": "test_user",
            "password": "wrong_password"
        }
    )
    assert response.status_code == 401

def test_protected_endpoint_without_token(test_client):
    """Testa acesso a endpoint protegido sem token"""
    response = test_client.get("/auth/me")
    assert response.status_code == 401

def test_protected_endpoint_with_token(test_client):
    """Testa acesso a endpoint protegido com token"""
    # Primeiro faz login para obter o token
    login_response = test_client.post(
        "/auth/login",
        data={
            "username": "test_user",
            "password": "correct_password"
        }
    )
    token = login_response.json()["access_token"]
    
    # Tenta acessar endpoint protegido
    response = test_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

def test_refresh_token(test_client):
    """Testa renovação de token"""
    # Primeiro faz login para obter os tokens
    login_response = test_client.post(
        "/auth/login",
        data={
            "username": "test_user",
            "password": "correct_password"
        }
    )
    refresh_token = login_response.json()["refresh_token"]
    
    # Tenta renovar o token
    response = test_client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()