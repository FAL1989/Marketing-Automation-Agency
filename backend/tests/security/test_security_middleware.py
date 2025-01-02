import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.middleware.security import SecurityMiddleware
from app.core.config import settings

@pytest.fixture
def app():
    app = FastAPI()
    app.add_middleware(SecurityMiddleware)
    
    @app.get("/test")
    def test_route():
        return {"message": "test"}
    
    @app.post("/test")
    def test_post_route(data: dict):
        return data
    
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_security_headers(client):
    """Testa se os headers de segurança estão presentes"""
    response = client.get("/test")
    assert response.status_code == 200
    
    # Verifica headers básicos de segurança
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    
    # Verifica HSTS
    assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
    assert "includeSubDomains" in response.headers["Strict-Transport-Security"]
    
    # Verifica Permissions Policy
    assert "accelerometer=()" in response.headers["Permissions-Policy"]
    assert "camera=()" in response.headers["Permissions-Policy"]
    
    # Verifica CORP headers
    assert response.headers["Cross-Origin-Embedder-Policy"] == "require-corp"
    assert response.headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert response.headers["Cross-Origin-Resource-Policy"] == "same-origin"

def test_content_security_policy(client):
    """Testa se o CSP está configurado corretamente"""
    response = client.get("/test")
    csp = response.headers["Content-Security-Policy"]
    
    # Verifica diretivas básicas
    assert "default-src 'self'" in csp
    assert "script-src 'self' 'unsafe-inline' 'unsafe-eval'" in csp
    assert "style-src 'self' 'unsafe-inline'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "base-uri 'self'" in csp
    assert "object-src 'none'" in csp

def test_csrf_protection(client):
    """Testa proteção CSRF"""
    # Requisição sem Origin deve passar
    response = client.get("/test")
    assert response.status_code == 200
    
    # POST com Origin inválido deve falhar
    response = client.post(
        "/test",
        json={"test": "data"},
        headers={"Origin": "http://malicious.com"}
    )
    assert response.status_code == 403
    assert "CSRF validation failed" in response.text
    
    # POST com Origin válido deve passar
    response = client.post(
        "/test",
        json={"test": "data"},
        headers={"Origin": settings.FRONTEND_URL}
    )
    assert response.status_code == 200

def test_xss_protection(client):
    """Testa proteção XSS"""
    # Dados normais devem passar
    response = client.post(
        "/test",
        json={"text": "normal text"}
    )
    assert response.status_code == 200
    
    # Tentativa de XSS deve falhar
    response = client.post(
        "/test",
        json={"text": "<script>alert('xss')</script>"}
    )
    assert response.status_code == 400
    assert "XSS attempt detected" in response.text
    
    # Tentativa de XSS com javascript: deve falhar
    response = client.post(
        "/test",
        json={"text": "javascript:alert('xss')"}
    )
    assert response.status_code == 400
    assert "XSS attempt detected" in response.text

def test_nested_xss_protection(client):
    """Testa proteção XSS em objetos aninhados"""
    # Objeto aninhado normal deve passar
    response = client.post(
        "/test",
        json={
            "nested": {
                "text": "normal text"
            }
        }
    )
    assert response.status_code == 200
    
    # Objeto aninhado com XSS deve falhar
    response = client.post(
        "/test",
        json={
            "nested": {
                "text": "<script>alert('xss')</script>"
            }
        }
    )
    assert response.status_code == 400
    assert "XSS attempt detected" in response.text 