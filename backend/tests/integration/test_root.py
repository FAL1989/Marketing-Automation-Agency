import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root(client):
    """Testa o endpoint raiz da API"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "AI Agency API",
        "version": "1.0.0",
        "docs_url": "/api/v1/docs"
    } 