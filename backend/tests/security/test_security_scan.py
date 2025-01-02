import pytest
import time
import subprocess
import json
import requests
from fastapi import FastAPI
from ...app.middleware.security import SecurityMiddleware
from ...app.middleware.rate_limit import RateLimitMiddleware
from ...app.core.config import settings
import uvicorn
import multiprocessing
import logging
from pathlib import Path
from typing import Dict, List
import docker

logger = logging.getLogger(__name__)

def create_test_app():
    """
    Cria uma aplicação FastAPI para testes
    """
    app = FastAPI()
    app.add_middleware(SecurityMiddleware)
    app.add_middleware(RateLimitMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    @app.post("/test")
    async def test_post_endpoint():
        return {"message": "test"}
    
    return app

def run_server(host: str, port: int):
    """
    Executa o servidor de teste
    """
    app = create_test_app()
    uvicorn.run(app, host=host, port=port)

@pytest.fixture(scope="module")
def server():
    """
    Fixture que inicia o servidor de teste
    """
    host = "localhost"
    port = 8000
    
    # Inicia o servidor em um processo separado
    process = multiprocessing.Process(
        target=run_server,
        args=(host, port)
    )
    process.start()
    
    # Aguarda o servidor iniciar
    time.sleep(2)
    
    yield f"http://{host}:{port}"
    
    # Encerra o servidor
    process.terminate()
    process.join()

@pytest.fixture(scope="module")
def zap_container():
    """
    Fixture que inicia o container do OWASP ZAP
    """
    client = docker.from_env()
    
    # Inicia o container do ZAP
    container = client.containers.run(
        "owasp/zap2docker-stable",
        "zap.sh -daemon -host 0.0.0.0 -port 8080 -config api.disablekey=true",
        ports={"8080/tcp": 8080},
        detach=True
    )
    
    # Aguarda o ZAP iniciar
    time.sleep(10)
    
    yield container
    
    # Remove o container
    container.stop()
    container.remove()

def start_zap_scan(target_url: str) -> Dict:
    """
    Inicia um scan do ZAP no alvo especificado
    """
    zap_api_url = "http://localhost:8080"
    
    # Configura o alvo
    requests.get(
        f"{zap_api_url}/JSON/spider/action/scan",
        params={"url": target_url}
    )
    
    # Aguarda o spider completar
    while True:
        status = requests.get(
            f"{zap_api_url}/JSON/spider/view/status"
        ).json()
        if status["status"] == "100":
            break
        time.sleep(1)
    
    # Inicia o scan ativo
    requests.get(
        f"{zap_api_url}/JSON/ascan/action/scan",
        params={"url": target_url}
    )
    
    # Aguarda o scan completar
    while True:
        status = requests.get(
            f"{zap_api_url}/JSON/ascan/view/status"
        ).json()
        if status["status"] == "100":
            break
        time.sleep(1)
    
    # Obtém os alertas
    alerts = requests.get(
        f"{zap_api_url}/JSON/alert/view/alerts"
    ).json()
    
    return alerts

def save_scan_results(results: Dict, output_file: str):
    """
    Salva os resultados do scan em um arquivo
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

def analyze_scan_results(results: Dict) -> List[Dict]:
    """
    Analisa os resultados do scan e retorna os problemas encontrados
    """
    issues = []
    
    for alert in results.get("alerts", []):
        severity = alert.get("risk")
        if severity in ["High", "Medium"]:
            issues.append({
                "name": alert.get("name"),
                "severity": severity,
                "description": alert.get("description"),
                "solution": alert.get("solution"),
                "evidence": alert.get("evidence"),
                "urls": alert.get("instances", [])
            })
    
    return issues

@pytest.mark.security
def test_security_scan(server, zap_container):
    """
    Executa um scan de segurança completo
    """
    # Executa o scan
    results = start_zap_scan(server)
    
    # Salva os resultados
    save_scan_results(
        results,
        "reports/security/zap_scan_results.json"
    )
    
    # Analisa os resultados
    issues = analyze_scan_results(results)
    
    # Registra os problemas encontrados
    if issues:
        logger.warning("Security issues found:")
        for issue in issues:
            logger.warning(
                f"  {issue['severity']} - {issue['name']}\n"
                f"  Description: {issue['description']}\n"
                f"  Solution: {issue['solution']}\n"
                f"  Evidence: {issue['evidence']}\n"
                f"  URLs: {', '.join(url['uri'] for url in issue['urls'])}\n"
            )
    
    # Falha o teste se houver problemas críticos
    critical_issues = [
        issue for issue in issues
        if issue["severity"] == "High"
    ]
    assert not critical_issues, (
        f"Found {len(critical_issues)} critical security issues"
    )

@pytest.mark.security
def test_security_headers(server):
    """
    Verifica a presença e configuração dos headers de segurança
    """
    response = requests.get(server)
    headers = response.headers
    
    # Headers obrigatórios
    required_headers = {
        "X-Frame-Options": ["DENY"],
        "X-Content-Type-Options": ["nosniff"],
        "X-XSS-Protection": ["1; mode=block"],
        "Referrer-Policy": ["strict-origin-when-cross-origin"],
        "Content-Security-Policy": None,  # Verificado separadamente
        "Permissions-Policy": None,  # Verificado separadamente
        "Cross-Origin-Embedder-Policy": ["require-corp"],
        "Cross-Origin-Opener-Policy": ["same-origin"],
        "Cross-Origin-Resource-Policy": ["same-origin"]
    }
    
    # Verifica a presença e valores dos headers
    for header, values in required_headers.items():
        assert header in headers, f"Missing security header: {header}"
        if values:
            assert headers[header] in values, (
                f"Invalid value for {header}: {headers[header]}"
            )
    
    # Verifica Content Security Policy
    csp = headers.get("Content-Security-Policy", "")
    assert "default-src 'self'" in csp
    assert "script-src" in csp
    assert "style-src" in csp
    assert "img-src" in csp
    assert "font-src" in csp
    assert "connect-src" in csp
    assert "frame-ancestors 'none'" in csp
    
    # Verifica Permissions Policy
    permissions = headers.get("Permissions-Policy", "")
    assert "accelerometer=()" in permissions
    assert "camera=()" in permissions
    assert "geolocation=()" in permissions

@pytest.mark.security
def test_rate_limit_protection(server):
    """
    Verifica se a proteção de rate limit está funcionando
    """
    # Faz requisições até exceder o limite
    responses = []
    for _ in range(settings.RATE_LIMIT_PER_MINUTE + 1):
        response = requests.get(server)
        responses.append(response.status_code)
    
    # Verifica se houve respostas 429
    assert 429 in responses, "Rate limit not enforced"
    
    # Verifica headers de rate limit
    response = requests.get(server)
    assert "X-Rate-Limit-Limit" in response.headers
    assert "X-Rate-Limit-Remaining" in response.headers
    assert "X-Rate-Limit-Reset" in response.headers 