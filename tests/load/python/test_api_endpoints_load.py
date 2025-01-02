import pytest
import pytest_asyncio
import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict
import logging
from app.core.config import settings
from app.models.user import User
from app.core.security import create_access_token
from fastapi.testclient import TestClient
from app.main import app
from app.core.circuit_breaker import CIRCUIT_BREAKER_REGISTRY

logger = logging.getLogger(__name__)

# URL base para os testes
BASE_URL = "http://localhost:8000"

@pytest.fixture(scope="function")
def test_app():
    """Fixture que fornece a aplicação de teste"""
    return TestClient(app)

@pytest_asyncio.fixture
async def auth_headers():
    """Fixture que fornece headers de autenticação"""
    # Cria usuário de teste
    async with aiohttp.ClientSession() as session:
        user_data = {
            "email": "loadtest@example.com",
            "password": "testpass123",
            "full_name": "Load Test User"
        }
        
        # Tenta fazer login primeiro
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        async with session.post(
            f"{BASE_URL}{settings.API_V1_STR}/auth/login",
            data=login_data,
            ssl=False
        ) as login_response:
            if login_response.status == 401:  # Usuário não existe
                # Registra o usuário
                async with session.post(
                    f"{BASE_URL}{settings.API_V1_STR}/auth/register",
                    json=user_data,
                    ssl=False
                ) as register_response:
                    register_data = await register_response.json()
                    access_token = register_data["access_token"]
            else:
                login_data = await login_response.json()
                access_token = login_data["access_token"]
    
    headers = {"Authorization": f"Bearer {access_token}"}
    logger.info(f"Generated auth headers: {headers}")
    return headers

async def make_concurrent_requests(
    url: str,
    total_requests: int,
    concurrent_requests: int,
    method: str = "GET",
    headers: Dict[str, str] = None,
    json_data: Dict = None
) -> List[Dict]:
    """Faz requisições concorrentes para um endpoint"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        results = []
        
        async def make_request():
            start_time = time.time()
            try:
                async with session.request(
                    method=method,
                    url=f"{BASE_URL}{url}",
                    headers=headers,
                    json=json_data,
                    ssl=False
                ) as response:
                    body = await response.read()
                    elapsed = time.time() - start_time
                    return {
                        "status": response.status,
                        "elapsed": elapsed,
                        "size": len(body),
                        "headers": dict(response.headers)
                    }
            except Exception as e:
                logger.error(f"Error making request: {str(e)}")
                return {
                    "status": 500,
                    "elapsed": time.time() - start_time,
                    "error": str(e)
                }
        
        # Cria todas as tasks de uma vez
        tasks = [make_request() for _ in range(total_requests)]
        
        # Processa em lotes de concurrent_requests
        for i in range(0, len(tasks), concurrent_requests):
            batch = tasks[i:i + concurrent_requests]
            batch_results = await asyncio.gather(*batch)
            results.extend(batch_results)
        
        return results

def analyze_results(results: List[Dict], endpoint: str):
    """Analisa os resultados dos testes de carga"""
    status_counts = {}
    latencies = []
    sizes = []
    
    for result in results:
        status = result["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
        if status == 200:
            latencies.append(result["elapsed"])
            if "size" in result:
                sizes.append(result["size"])
    
    logger.info(f"\nResultados para {endpoint}:")
    logger.info(f"Status codes: {status_counts}")
    
    if latencies:
        logger.info(f"Latência (segundos):")
        logger.info(f"  Min: {min(latencies):.3f}")
        logger.info(f"  Max: {max(latencies):.3f}")
        logger.info(f"  Avg: {statistics.mean(latencies):.3f}")
        logger.info(f"  Med: {statistics.median(latencies):.3f}")
        logger.info(f"  P95: {statistics.quantiles(latencies, n=20)[18]:.3f}")
        
    if sizes:
        avg_size = statistics.mean(sizes)
        logger.info(f"Tamanho médio da resposta: {avg_size/1024:.2f}KB")
    
    return {
        "success_rate": status_counts.get(200, 0) / len(results),
        "avg_latency": statistics.mean(latencies) if latencies else None,
        "p95_latency": statistics.quantiles(latencies, n=20)[18] if latencies else None
    }

@pytest.mark.asyncio
async def test_health_check_load():
    """Teste de carga do endpoint de health check"""
    url = f"{settings.API_V1_STR}/health-check"
    results = await make_concurrent_requests(
        url=url,
        total_requests=100,  # Reduzindo para teste inicial
        concurrent_requests=10
    )
    
    metrics = analyze_results(results, "health check")
    assert metrics["success_rate"] > 0.99, "Taxa de sucesso deve ser maior que 99%"
    assert metrics["avg_latency"] < 0.1, "Latência média deve ser menor que 100ms"
    assert metrics["p95_latency"] < 0.2, "P95 deve ser menor que 200ms"

@pytest.mark.asyncio
async def test_template_list_load(auth_headers):
    """Teste de carga do endpoint de listagem de templates"""
    url = f"{settings.API_V1_STR}/templates"  # Endpoint correto do router
    logger.info(f"Making requests to {url} with headers: {auth_headers}")
    
    results = await make_concurrent_requests(
        url=url,
        total_requests=50,  # Reduzindo para teste inicial
        concurrent_requests=5,
        headers=auth_headers
    )
    
    metrics = analyze_results(results, "template list")
    assert metrics["success_rate"] > 0.95, "Taxa de sucesso deve ser maior que 95%"
    assert metrics["avg_latency"] < 0.2, "Latência média deve ser menor que 200ms"
    assert metrics["p95_latency"] < 0.5, "P95 deve ser menor que 500ms"

@pytest.mark.asyncio
async def test_content_generation_load(auth_headers):
    """Teste de carga do endpoint de geração de conteúdo"""
    # Primeiro cria um template
    template_url = f"{settings.API_V1_STR}/templates"
    template_data = {
        "name": "Test Template",
        "content": "This is a test template with {{test}} variable",
        "description": "Template for load testing"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}{template_url}",
            headers=auth_headers,
            json=template_data,
            ssl=False
        ) as response:
            response_text = await response.text()
            logger.info(f"Template creation response: {response.status} - {response_text}")
            template = await response.json()
            template_id = template["id"]
    
    # Agora testa a geração de conteúdo
    url = f"{settings.API_V1_STR}/contents"
    json_data = {
        "template_id": template_id,
        "variables": {"test": "value"}
    }
    
    results = await make_concurrent_requests(
        url=url,
        total_requests=20,  # Reduzindo para teste inicial
        concurrent_requests=2,
        method="POST",
        headers=auth_headers,
        json_data=json_data
    )
    
    metrics = analyze_results(results, "content generation")
    assert metrics["success_rate"] > 0.90, "Taxa de sucesso deve ser maior que 90%"
    assert metrics["avg_latency"] < 1.0, "Latência média deve ser menor que 1s"
    assert metrics["p95_latency"] < 2.0, "P95 deve ser menor que 2s" 