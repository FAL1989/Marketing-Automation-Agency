import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.user import User

client = TestClient(app)

def test_login(test_user: User):
    """Testa o endpoint de login com credenciais válidas"""
    response = client.post(
        "/auth/login",
        data={
            "username": "test@example.com",
            "password": "testpassword"
        }
    )
    assert response.status_code == 200
    json_response = response.json()
    assert "access_token" in json_response
    assert json_response["token_type"] == "bearer"

def test_login_invalid_credentials(test_user: User):
    """Testa o login com credenciais inválidas"""
    response = client.post(
        "/auth/login",
        data={
            "username": "invalid@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciais inválidas" 