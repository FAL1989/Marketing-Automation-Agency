import pytest
from fastapi.testclient import TestClient
from backend.app.main import create_app
import json
import io

@pytest.fixture
def test_client():
    """Cria um cliente de teste"""
    app = create_app()
    return TestClient(app)

def test_valid_json_payload(test_client):
    """Testa payload JSON válido"""
    response = test_client.post(
        "/api/test",
        json={"name": "test", "value": 123}
    )
    assert response.status_code != 400

def test_invalid_json_format(test_client):
    """Testa payload JSON inválido"""
    response = test_client.post(
        "/api/test",
        headers={"Content-Type": "application/json"},
        content="invalid json"
    )
    assert response.status_code == 400
    assert "Invalid JSON format" in response.text

def test_json_depth_limit(test_client):
    """Testa limite de profundidade JSON"""
    # Cria um JSON profundo
    deep_json = {}
    current = deep_json
    for i in range(25):  # Mais profundo que o limite de 20
        current["next"] = {}
        current = current["next"]
    
    response = test_client.post("/api/test", json=deep_json)
    assert response.status_code == 400
    assert "JSON structure too deep" in response.text

def test_suspicious_json_patterns(test_client):
    """Testa detecção de padrões suspeitos em JSON"""
    suspicious_payloads = [
        {"__proto__": "attack"},
        {"$where": "this.hack"},
        {"field": {"$gt": 100}},
        {"constructor": {"prototype": "hack"}}
    ]
    
    for payload in suspicious_payloads:
        response = test_client.post("/api/test", json=payload)
        assert response.status_code == 400
        assert "Suspicious pattern detected" in response.text

def test_file_size_limit(test_client):
    """Testa limite de tamanho de arquivo"""
    # Cria um arquivo maior que o limite
    large_file = io.BytesIO(b"0" * (6 * 1024 * 1024))  # 6MB
    files = {"file": ("test.txt", large_file, "text/plain")}
    
    response = test_client.post("/api/upload", files=files)
    assert response.status_code == 413
    assert "File too large" in response.text

def test_file_type_validation(test_client):
    """Testa validação de tipo de arquivo"""
    # Arquivo com tipo não permitido
    files = {
        "file": ("test.exe", b"malicious content", "application/x-msdownload")
    }
    
    response = test_client.post("/api/upload", files=files)
    assert response.status_code == 415
    assert "File type not allowed" in response.text

def test_html_sanitization(test_client):
    """Testa sanitização de HTML"""
    # HTML com tags maliciosas
    payload = {
        "content": "<p>Valid content</p><script>alert('xss')</script>"
    }
    
    response = test_client.post("/api/content", json=payload)
    assert response.status_code != 400
    
    # Verifica se o script foi removido
    result = response.json()
    assert "<script>" not in result["content"]
    assert "Valid content" in result["content"]

def test_payload_size_limit(test_client):
    """Testa limite de tamanho do payload"""
    # Cria um payload maior que o limite
    large_payload = {"data": "x" * (11 * 1024 * 1024)}  # 11MB
    
    response = test_client.post("/api/test", json=large_payload)
    assert response.status_code == 413
    assert "Payload too large" in response.text

def test_valid_file_upload(test_client):
    """Testa upload de arquivo válido"""
    # Arquivo PNG válido
    files = {
        "file": ("test.png", b"PNG content", "image/png")
    }
    
    response = test_client.post("/api/upload", files=files)
    assert response.status_code != 415
    assert response.status_code != 413

def test_multiple_file_validation(test_client):
    """Testa validação de múltiplos arquivos"""
    files = {
        "file1": ("test1.png", b"PNG content", "image/png"),
        "file2": ("test2.jpg", b"JPG content", "image/jpeg"),
        "file3": ("test3.exe", b"EXE content", "application/x-msdownload")
    }
    
    response = test_client.post("/api/upload", files=files)
    assert response.status_code == 415  # Falha no arquivo .exe

def test_unicode_injection(test_client):
    """Testa injeção de caracteres Unicode maliciosos"""
    payload = {
        "content": "Test \u0000 null byte injection"
    }
    
    response = test_client.post("/api/test", json=payload)
    assert response.status_code == 400

@pytest.mark.parametrize("content_type,expected_status", [
    ("application/json", 200),
    ("text/plain", 200),
    ("application/x-www-form-urlencoded", 200),
    ("application/octet-stream", 415)
])
def test_content_type_validation(test_client, content_type, expected_status):
    """Testa validação de diferentes Content-Types"""
    headers = {"Content-Type": content_type}
    response = test_client.post("/api/test", headers=headers, data="test")
    assert response.status_code == expected_status 