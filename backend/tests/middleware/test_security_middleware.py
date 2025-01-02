import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from ...app.middleware.security import SecurityMiddleware
from ...app.monitoring.security_metrics import SecurityMetrics
from unittest.mock import Mock, patch

@pytest.fixture
def app():
    """
    Fixture que cria uma aplicação FastAPI com o SecurityMiddleware
    """
    app = FastAPI()
    app.add_middleware(SecurityMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    @app.post("/test")
    async def test_post_endpoint():
        return {"message": "test"}
    
    return app

@pytest.fixture
def client(app):
    """
    Fixture que cria um cliente de teste
    """
    return TestClient(app)

def test_security_headers(client):
    """
    Testa se os headers de segurança estão sendo adicionados corretamente
    """
    response = client.get("/test")
    assert response.status_code == 200
    
    # Verifica headers de segurança
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "accelerometer=()" in response.headers["Permissions-Policy"]
    assert response.headers["Cross-Origin-Embedder-Policy"] == "require-corp"
    assert response.headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert response.headers["Cross-Origin-Resource-Policy"] == "same-origin"
    
    # Verifica Content Security Policy
    csp = response.headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp
    assert "script-src 'self' 'unsafe-inline' 'unsafe-eval'" in csp
    assert "style-src 'self' 'unsafe-inline'" in csp
    assert "img-src 'self' data: https:" in csp
    assert "font-src 'self' data:" in csp
    assert "connect-src 'self' https:" in csp
    assert "frame-ancestors 'none'" in csp
    assert "base-uri 'self'" in csp
    assert "form-action 'self'" in csp

@patch.object(SecurityMetrics, "record_xss_attempt")
def test_xss_detection(mock_record_xss, client):
    """
    Testa a detecção de tentativas de XSS
    """
    # Testa XSS via query params
    response = client.get("/test?q=<script>alert('xss')</script>")
    assert response.status_code == 200
    mock_record_xss.assert_called_once()
    
    # Testa XSS via headers
    mock_record_xss.reset_mock()
    headers = {"User-Agent": "<script>alert('xss')</script>"}
    response = client.get("/test", headers=headers)
    assert response.status_code == 200
    mock_record_xss.assert_called_once()

@patch.object(SecurityMetrics, "record_csrf_attempt")
def test_csrf_detection(mock_record_csrf, client):
    """
    Testa a detecção de tentativas de CSRF
    """
    # Testa requisição POST sem Origin e Referer
    response = client.post("/test")
    assert response.status_code == 200
    mock_record_csrf.assert_called_once()
    
    # Testa requisição POST com Origin
    mock_record_csrf.reset_mock()
    headers = {"Origin": "http://localhost"}
    response = client.post("/test", headers=headers)
    assert response.status_code == 200
    mock_record_csrf.assert_not_called()

@patch.object(SecurityMetrics, "record_unauthorized_access")
def test_unauthorized_access_detection(mock_record_unauthorized, client):
    """
    Testa a detecção de tentativas de acesso não autorizado
    """
    # Testa acesso sem Authorization header
    response = client.get("/test")
    assert response.status_code == 200
    mock_record_unauthorized.assert_called_once()
    
    # Testa acesso com Authorization header
    mock_record_unauthorized.reset_mock()
    headers = {"Authorization": "Bearer token"}
    response = client.get("/test", headers=headers)
    assert response.status_code == 200
    mock_record_unauthorized.assert_not_called()

@patch.object(SecurityMetrics, "record_request_latency")
def test_request_latency_recording(mock_record_latency, client):
    """
    Testa o registro de latência das requisições
    """
    response = client.get("/test")
    assert response.status_code == 200
    mock_record_latency.assert_called_once()
    
    # Verifica os argumentos da chamada
    args = mock_record_latency.call_args[1]
    assert "path" in args
    assert "method" in args
    assert "start_time" in args
    assert args["path"] == "/test"
    assert args["method"] == "GET" 