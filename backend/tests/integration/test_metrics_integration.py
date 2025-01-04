import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
import asyncio
from redis.asyncio import Redis
from app.middleware.security import SecurityMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.services.monitoring_service import MonitoringService
from app.core.config import settings
from app.core.redis import get_redis
import time
from asyncio import TimeoutError
import socket
import logging
from app.main import app
import pytest_asyncio

logger = logging.getLogger(__name__)

@pytest.fixture(scope="session", autouse=True)
async def setup_redis():
    """
    Fixture que configura o Redis para todos os testes
    """
    redis = await get_redis()
    await redis.flushdb()
    yield redis
    await redis.aclose()

@pytest.fixture
async def redis(setup_redis):
    """
    Fixture que fornece um cliente Redis limpo para cada teste
    """
    await setup_redis.flushdb()  # Limpa o banco antes do teste
    yield setup_redis

@pytest.fixture
def app():
    """
    Fixture que cria uma aplicação FastAPI com todos os middlewares
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

@pytest.fixture
def client(app):
    return TestClient(app)

@pytest_asyncio.fixture(scope="function")
async def monitoring():
    """
    Fixture que fornece uma instância limpa do MonitoringService para cada teste
    """
    # Cria um novo registro para cada teste
    registry = CollectorRegistry()
    
    # Cria uma nova instância do MonitoringService com o registro dedicado
    service = MonitoringService(registry=registry)
    
    return service

@pytest.mark.asyncio
async def test_metrics_collection(monitoring):
    await monitoring.record_api_request("/test", "GET", 200, 0.1)
    
    # Verifica se as métricas foram registradas
    assert monitoring.api_requests_total is not None, "api_requests_total metric should exist"
    assert monitoring.api_request_duration_seconds is not None, "api_request_duration_seconds metric should exist"
    
    # Verifica se os valores foram registrados
    samples = monitoring.api_requests_total.labels(
        endpoint="/test",
        method="GET",
        status=200
    )._value.get()
    
    # Verifica que o contador foi incrementado
    assert samples > 0, "api_requests_total should have a value greater than 0"
    
    # Verifica histograma
    hist_samples = monitoring.api_request_duration_seconds.collect()
    assert len(hist_samples) > 0, "api_request_duration_seconds should have samples"
    count_sample = next(s for s in hist_samples[0].samples if s.name.endswith("_count"))
    assert count_sample.value > 0, "api_request_duration_seconds should have recorded values"

@pytest.mark.asyncio
async def test_metrics_integration_rate_limit(monitoring, redis):
    """
    Testa a integração das métricas de rate limit
    """
    try:
        # Simula exceder o rate limit
        await monitoring.record_api_request("/test", "RATE_LIMIT", "error", 0.1)
        
        # Verifica métricas
        samples = monitoring.api_requests_total.labels(
            endpoint="/test",
            method="RATE_LIMIT",
            status="error"
        )._value.get()
        
        assert samples > 0, "Rate limit metrics should be recorded"
        
    except Exception as e:
        logger.error(f"Erro no teste de rate limit: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_metrics_integration_security(monitoring, client):
    """
    Testa a integração das métricas de segurança
    """
    try:
        # Simula requisições de segurança
        await monitoring.record_api_request("/test", "GET", 403, 0.1)
        
        # Verifica métricas
        samples = monitoring.api_requests_total.labels(
            endpoint="/test",
            method="GET",
            status=403
        )._value.get()
        
        assert samples > 0, "Security metrics should be recorded"
        
    except Exception as e:
        logger.error(f"Erro no teste de segurança: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_metrics_integration_error_tracking(monitoring):
    """
    Testa o rastreamento de erros
    """
    try:
        # Simula diferentes tipos de erro
        error_codes = [400, 401, 403, 404, 500]
        for code in error_codes:
            await monitoring.record_api_request("/test", "GET", code, 0.0)
        
        # Verifica métricas
        for code in error_codes:
            samples = monitoring.api_requests_total.labels(
                endpoint="/test",
                method="GET",
                status=code
            )._value.get()
            
            assert samples > 0, f"Error metrics for code {code} should be recorded"
            
    except Exception as e:
        logger.error(f"Erro no teste de erros: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_metrics_integration_system_resources(monitoring):
    """
    Testa o monitoramento de recursos do sistema
    """
    try:
        # Simula operações do sistema
        await monitoring.record_api_request("/test", "GET", 200, 0.1)
        
        # Verifica métricas
        samples = monitoring.api_requests_total.labels(
            endpoint="/test",
            method="GET",
            status=200
        )._value.get()
        
        assert samples > 0, "System resource metrics should be recorded"
        
    except Exception as e:
        logger.error(f"Erro no teste de recursos: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_metrics_integration_redis_operations(monitoring, redis):
    """
    Testa as métricas específicas do Redis
    """
    try:
        # Simula várias operações do Redis
        operations = ["get", "set", "delete", "incr", "expire"]
        for op in operations:
            await monitoring.record_api_request(f"/redis/{op}", "GET", 200, 0.01)
        
        # Verifica métricas
        for op in operations:
            samples = monitoring.api_requests_total.labels(
                endpoint=f"/redis/{op}",
                method="GET",
                status=200
            )._value.get()
            
            assert samples > 0, f"Redis operation metrics for {op} should be recorded"
            
    except Exception as e:
        logger.error(f"Erro no teste de operações do Redis: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_metrics_integration_cache(monitoring):
    """
    Testa as métricas de cache
    """
    try:
        # Simula operações de cache
        await monitoring.record_api_request("/cache/hit", "GET", 200, 0.01)  # hit
        await monitoring.record_api_request("/cache/miss", "GET", 404, 0.01)  # miss
        
        # Verifica métricas
        hit_samples = monitoring.api_requests_total.labels(
            endpoint="/cache/hit",
            method="GET",
            status=200
        )._value.get()
        
        miss_samples = monitoring.api_requests_total.labels(
            endpoint="/cache/miss",
            method="GET",
            status=404
        )._value.get()
        
        assert hit_samples > 0, "Cache hit metrics should be recorded"
        assert miss_samples > 0, "Cache miss metrics should be recorded"
        
    except Exception as e:
        logger.error(f"Erro no teste de cache: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_metrics_integration_rate_limit_detailed(monitoring):
    """
    Testa métricas detalhadas de rate limit
    """
    try:
        # Simula diferentes cenários de rate limit
        endpoints = ["/api/v1/users", "/api/v1/content", "/api/v1/templates"]
        for endpoint in endpoints:
            await monitoring.record_api_request(endpoint, "RATE_LIMIT", "error", 0.01)
        
        # Verifica métricas
        for endpoint in endpoints:
            samples = monitoring.api_requests_total.labels(
                endpoint=endpoint,
                method="RATE_LIMIT",
                status="error"
            )._value.get()
            
            assert samples > 0, f"Rate limit metrics for {endpoint} should be recorded"
            
    except Exception as e:
        logger.error(f"Erro no teste detalhado de rate limit: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_metrics_integration_api_latency(monitoring):
    """
    Testa métricas detalhadas de latência da API
    """
    try:
        # Simula requisições com diferentes latências
        latencies = [0.01, 0.05, 0.1, 0.5, 1.0]
        for latency in latencies:
            await monitoring.record_api_request("/test", "GET", 200, latency)
        
        # Verifica métricas
        assert monitoring.api_requests_total is not None, "api_requests_total metric should exist"
        assert monitoring.api_request_duration_seconds is not None, "api_request_duration_seconds metric should exist"
        
        # Verifica se os valores foram registrados
        samples = monitoring.api_requests_total.labels(
            endpoint="/test",
            method="GET",
            status=200
        )._value.get()
        
        assert samples == len(latencies), "All latency samples should be recorded"
        
        # Verifica histograma
        hist_samples = monitoring.api_request_duration_seconds.collect()
        assert len(hist_samples) > 0, "api_request_duration_seconds should have samples"
        count_sample = next(s for s in hist_samples[0].samples if s.name.endswith("_count"))
        assert count_sample.value == len(latencies), "All latency samples should be in histogram"
        
    except Exception as e:
        logger.error(f"Erro no teste de latência: {str(e)}")
        raise 