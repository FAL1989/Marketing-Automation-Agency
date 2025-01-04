import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from prometheus_client import Counter, Histogram, Gauge
import asyncio
from redis.asyncio import Redis
from app.middleware.security import SecurityMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.monitoring.metrics import PerformanceMetrics
from app.core.monitoring import MonitoringService
from app.services.rate_limiter import TokenBucketRateLimiter
from app.core.config import settings
from app.core.redis import get_redis
import time
from asyncio import TimeoutError
import socket
import logging
from app.main import app

logger = logging.getLogger(__name__)

@pytest.fixture(scope="session", autouse=True)
async def setup_redis():
    """
    Fixture que configura o Redis para todos os testes
    """
    redis = await get_redis()
    yield
    await redis.close()

@pytest.fixture
async def redis():
    """
    Fixture que fornece um cliente Redis limpo para cada teste
    """
    redis = await get_redis()
    await redis.flushdb()  # Limpa o banco antes do teste
    yield redis
    await redis.close()

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

@pytest.fixture
def metrics_service():
    return PerformanceMetrics()

@pytest.mark.asyncio
async def test_metrics_collection():
    monitoring = MonitoringService()
    await monitoring.record_api_request("/test", "GET", 200, 0.1)
    
    response = client.get("/metrics")
    assert response.status_code == 200
    metrics_text = response.text
    
    assert 'api_requests_total' in metrics_text
    assert 'api_request_duration_seconds' in metrics_text

@pytest.mark.asyncio
async def test_metrics_integration_rate_limit(client, redis):
    """
    Testa a integração das métricas de rate limit
    """
    try:
        # Limpa o Redis antes do teste
        await redis.flushdb()
        
        monitoring = MonitoringService()
        rate_limiter = TokenBucketRateLimiter(monitoring)
        
        # Faz requisições até exceder o rate limit
        for i in range(settings.RATE_LIMIT_REQUESTS + 1):
            allowed, headers = await rate_limiter.check_rate_limit("test")
            if not allowed:
                assert headers["X-RateLimit-Remaining"] == "0"
                break
        
        # Verifica métricas
        assert monitoring.rate_limit_exceeded_total._value.get() > 0
        assert monitoring.rate_limit_current._value.get() > 0
        
    except Exception as e:
        logger.error(f"Erro no teste de rate limit: {e}")
        pytest.fail(f"Erro no teste de rate limit: {e}")

@pytest.mark.asyncio
async def test_metrics_integration_security(client):
    """
    Testa a integração das métricas de segurança
    """
    try:
        monitoring = MonitoringService()
        
        # Simula múltiplos IPs fazendo requisições
        ips = [f"192.168.1.{i}" for i in range(5)]
        
        for ip in ips:
            # Tenta um ataque XSS com IP diferente
            response = client.get(
                "/test?q=<script>alert('xss')</script>",
                headers={"X-Forwarded-For": ip}
            )
            assert response.status_code == 200
            
            # Tenta um ataque CSRF com IP diferente
            response = client.post(
                "/test",
                headers={"X-Forwarded-For": ip}
            )
            assert response.status_code == 200
            
            # Tenta acesso não autorizado com IP diferente
            response = client.get(
                "/test",
                headers={"X-Forwarded-For": ip}
            )
            assert response.status_code == 200
        
        # Verifica métricas
        assert monitoring.api_requests_total._value.get() > 0
        
    except Exception as e:
        logger.error(f"Erro no teste de segurança: {e}")
        pytest.fail(f"Erro no teste de segurança: {e}")

@pytest.mark.asyncio
async def test_metrics_integration_latency_distribution(client):
    """
    Testa a distribuição de latência das requisições
    """
    try:
        monitoring = MonitoringService()
        
        # Simula requisições com diferentes latências
        latencies = [0.1, 0.2, 0.5, 1.0, 2.0]
        for latency in latencies:
            await monitoring.record_api_request("/test", "GET", 200, latency)
        
        # Verifica métricas
        assert monitoring.api_request_duration_seconds._sum.get() > 0
        
    except Exception as e:
        logger.error(f"Erro no teste de latência: {e}")
        pytest.fail(f"Erro no teste de latência: {e}")

@pytest.mark.asyncio
async def test_metrics_integration_error_tracking(client):
    """
    Testa o rastreamento de erros
    """
    try:
        monitoring = MonitoringService()
        
        # Simula diferentes tipos de erro
        error_codes = [400, 401, 403, 404, 500]
        for code in error_codes:
            await monitoring.record_api_request("/test", "GET", code, 0.1)
        
        # Verifica métricas
        assert monitoring.api_requests_total._value.get() > 0
        
    except Exception as e:
        logger.error(f"Erro no teste de erros: {e}")
        pytest.fail(f"Erro no teste de erros: {e}")

@pytest.mark.asyncio
async def test_metrics_integration_system_resources(client):
    """
    Testa o monitoramento de recursos do sistema
    """
    try:
        monitoring = MonitoringService()
        
        # Simula algumas operações
        await monitoring.record_api_request("/test", "GET", 200, 0.1)
        await monitoring.record_redis_operation("get", 0.01)
        await monitoring.update_redis_stats({"connected_clients": 1, "used_memory": 1024})
        
        # Verifica métricas
        assert monitoring.api_requests_total._value.get() > 0
        assert monitoring.redis_operations_total._value.get() > 0
        assert monitoring.redis_connections._value.get() > 0
        assert monitoring.redis_memory_usage_bytes._value.get() > 0
        
    except Exception as e:
        logger.error(f"Erro no teste de recursos: {e}")
        pytest.fail(f"Erro no teste de recursos: {e}") 