import pytest

def test_security_headers(client):
    """Testa se os headers de segurança estão presentes e corretos"""
    response = client.get("/")
    headers = response.headers
    
    # Headers obrigatórios
    assert "content-security-policy" in headers
    assert "x-frame-options" in headers
    assert "x-content-type-options" in headers
    assert "x-xss-protection" in headers
    assert "referrer-policy" in headers
    assert "x-permitted-cross-domain-policies" in headers
    assert "cross-origin-embedder-policy" in headers
    assert "cross-origin-opener-policy" in headers
    assert "cross-origin-resource-policy" in headers
    
    # Valores específicos
    assert headers["x-frame-options"] == "DENY"
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-xss-protection"] == "1; mode=block"
    assert headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert headers["x-permitted-cross-domain-policies"] == "none"
    assert headers["cross-origin-embedder-policy"] == "require-corp"
    assert headers["cross-origin-opener-policy"] == "same-origin"
    assert headers["cross-origin-resource-policy"] == "same-origin"

def test_csp_header(client):
    """Testa o Content Security Policy"""
    response = client.get("/")
    csp = response.headers["content-security-policy"]
    
    # Verifica diretivas obrigatórias
    assert "default-src 'self'" in csp
    assert "img-src 'self' data: https:" in csp
    assert "script-src 'self' 'unsafe-inline' 'unsafe-eval'" in csp
    assert "style-src 'self' 'unsafe-inline'" in csp
    assert "object-src 'none'" in csp
    assert "base-uri 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "form-action 'self'" in csp

def test_cache_control(client):
    """Testa os headers de cache control"""
    # GET request
    get_response = client.get("/")
    assert "cache-control" in get_response.headers
    assert get_response.headers["cache-control"] == "no-store, max-age=0"
    
    # POST request
    post_response = client.post("/")
    assert "cache-control" in post_response.headers
    assert "no-store" in post_response.headers["cache-control"]
    assert "no-cache" in post_response.headers["cache-control"]
    assert "must-revalidate" in post_response.headers["cache-control"]

def test_cors_headers(client):
    """Testa os headers CORS"""
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "X-Requested-With"
    }
    
    # OPTIONS request (preflight)
    response = client.options("/", headers=headers)
    
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers
    assert "access-control-max-age" in response.headers
    
    # Verifica valores específicos
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "POST" in response.headers["access-control-allow-methods"]
    assert "X-Requested-With" in response.headers["access-control-allow-headers"]

def test_cors_blocked_origin(client):
    """Testa bloqueio de origens não permitidas"""
    headers = {
        "Origin": "http://malicious-site.com"
    }
    
    response = client.get("/", headers=headers)
    assert "access-control-allow-origin" not in response.headers

def test_https_headers(client):
    """Testa headers específicos para HTTPS"""
    # Simula uma requisição HTTPS
    response = client.get("/", headers={"X-Forwarded-Proto": "https"})
    
    # Verifica HSTS
    assert "strict-transport-security" in response.headers
    hsts = response.headers["strict-transport-security"]
    assert "max-age=31536000" in hsts
    assert "includeSubDomains" in hsts
    assert "preload" in hsts 