import pytest
from fastapi.testclient import TestClient
from backend.app.main import create_app
from backend.app.core import monitoring

@pytest.fixture
def test_client(mock_redis):
    """Cria um cliente de teste com Redis mockado"""
    app = create_app()
    return TestClient(app)

def test_cors_allowed_origin(test_client):
    """Testa CORS com origem permitida"""
    response = test_client.options(
        "/metrics",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

def test_cors_blocked_origin(test_client):
    """Testa CORS com origem bloqueada"""
    response = test_client.options(
        "/metrics",
        headers={
            "Origin": "http://malicious-site.com",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert response.status_code == 400

def test_security_headers(test_client):
    """Testa se todos os headers de segurança estão presentes"""
    response = test_client.get("/")
    
    # Headers básicos
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    
    # Novos headers
    assert "Content-Security-Policy" in response.headers
    assert "Strict-Transport-Security" in response.headers
    assert response.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains; preload"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "Permissions-Policy" in response.headers
    assert response.headers["Cross-Origin-Resource-Policy"] == "same-origin"
    assert response.headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert response.headers["Cross-Origin-Embedder-Policy"] == "require-corp"

def test_csp_header_content(test_client):
    """Testa o conteúdo do Content Security Policy"""
    response = test_client.get("/")
    csp = response.headers["Content-Security-Policy"]
    
    # Verifica diretivas essenciais
    assert "default-src 'self'" in csp
    assert "script-src 'self' 'unsafe-inline' 'unsafe-eval'" in csp
    assert "object-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "base-uri 'self'" in csp

def test_permissions_policy_content(test_client):
    """Testa o conteúdo do Permissions Policy"""
    response = test_client.get("/")
    permissions = response.headers["Permissions-Policy"]
    
    # Verifica permissões restritas
    assert "camera=()" in permissions
    assert "geolocation=()" in permissions
    assert "microphone=()" in permissions
    assert "payment=()" in permissions

def test_suspicious_sql_injection(test_client):
    """Testa bloqueio de SQL injection"""
    response = test_client.get("/users/search?query=UNION SELECT")
    assert response.status_code == 403

def test_suspicious_xss(test_client):
    """Testa bloqueio de XSS"""
    response = test_client.get("/users/search?query=<script>alert(1)</script>")
    assert response.status_code == 403

def test_path_traversal(test_client):
    """Testa bloqueio de path traversal"""
    response = test_client.get("/users/search?query=../etc/passwd")
    assert response.status_code == 403

def test_host_validation(test_client):
    """Testa validação de host"""
    response = test_client.get(
        "/metrics",
        headers={"Host": "localhost:8000"}
    )
    assert response.status_code == 200

@pytest.mark.parametrize("pattern", [
    "UNION SELECT",
    "exec xp_",
    "../etc/passwd",
    "<script>alert(1)</script>",
    "../../secret",
    "%2e%2e%2f"
])
def test_suspicious_patterns(test_client, pattern):
    """Testa bloqueio de padrões suspeitos"""
    response = test_client.get(f"/users/search?query={pattern}")
    assert response.status_code == 403

def test_rate_limit_metrics(test_client):
    """Testa métricas de rate limit"""
    # Faz várias requisições para atingir o limite
    for _ in range(100):
        response = test_client.get("/metrics")
        assert response.status_code == 200
    
    # A próxima requisição deve ser bloqueada
    response = test_client.get("/metrics")
    assert response.status_code == 429 