import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_read_root():
    """Testa o endpoint raiz da API"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Bem-vindo à API",
        "version": "1.0.0",
        "status": "online"
    } 