import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY
import asyncio
from redis.asyncio import Redis
from app.middleware.security import SecurityMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.monitoring.metrics_exporter import metrics_exporter
from app.monitoring.security_metrics import security_registry
from app.services.rate_limiter import RATE_LIMIT_REGISTRY
from app.core.config import settings
from app.core.redis import redis_manager
import time
from asyncio import TimeoutError
import socket
import logging

logger = logging.getLogger(__name__)

@pytest.fixture(scope="session", autouse=True)
async def setup_redis():
    """
    Fixture que configura o Redis para todos os testes
    """
    await redis_manager.initialize()
    yield
    await redis_manager.close()

@pytest.fixture
async def redis():
    """
    Fixture que fornece um cliente Redis limpo para cada teste
    """
    client = await redis_manager.get_connection('rate_limit')
    await client.flushdb()  # Limpa o banco antes do teste
    yield client
    await client.close()

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
async def client(app):
    """
    Fixture que cria um cliente de teste
    """
    try:
        # Desliga qualquer servidor de métricas existente
        await metrics_exporter.shutdown()
        await asyncio.sleep(0.1)  # Pequeno delay para garantir que o servidor foi desligado
        
        # Encontra uma porta livre
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            port = s.getsockname()[1]
        
        # Inicia o servidor de métricas com timeout
        async with asyncio.timeout(5):
            await metrics_exporter.start(app, port)
            logger.info(f"Metrics server started on port {port}")
        
        client = TestClient(app)
        yield client
        
        # Desliga o servidor de métricas com timeout
        async with asyncio.timeout(5):
            await metrics_exporter.shutdown()
            await asyncio.sleep(0.1)  # Pequeno delay para garantir que o servidor foi desligado
            logger.info("Metrics server stopped")
    except TimeoutError:
        logger.error("Timeout ao iniciar/parar servidor de métricas")
        pytest.fail("Timeout ao iniciar/parar servidor de métricas")
    except Exception as e:
        logger.error(f"Erro ao configurar cliente de teste: {e}")
        pytest.fail(f"Erro ao configurar cliente de teste: {e}")

@pytest.mark.asyncio
async def test_metrics_integration_rate_limit(client, redis):
    """
    Testa a integração das métricas de rate limit
    """
    try:
        # Limpa o Redis antes do teste
        await redis.flushdb()
        
        # Faz requisições até exceder o rate limit com timeout
        async with asyncio.timeout(10):
            for i in range(settings.RATE_LIMIT_MAX_REQUESTS + 1):
                response = client.get("/test")
                logger.info(f"Request {i+1}: status={response.status_code}")
                if response.status_code == 429:
                    break
                await asyncio.sleep(0.05)  # Pequeno delay entre requisições
        
        # Aguarda propagação das métricas
        await asyncio.sleep(0.1)
        
        # Verifica se as métricas foram registradas
        metrics = {
            metric.name: metric
            for metric in RATE_LIMIT_REGISTRY.collect()
            if metric.name in [
                "rate_limit_hits",
                "rate_limit_blocked",
                "rate_limit_current",
                "rate_limit_latency"
            ]
        }
        
        # Verifica métricas de rate limit
        assert "rate_limit_hits" in metrics, "Métrica de hits de rate limit não encontrada"
        assert "rate_limit_blocked" in metrics, "Métrica de bloqueios de rate limit não encontrada"
        assert "rate_limit_current" in metrics, "Métrica de estado atual de rate limit não encontrada"
        assert "rate_limit_latency" in metrics, "Métrica de latência de rate limit não encontrada"
        
        # Verifica se houve hits registrados
        hits_samples = list(metrics["rate_limit_hits"].samples)
        assert any(
            sample.value > 0
            for sample in hits_samples
            if sample.labels["route"] == "/test"
        ), "Nenhum hit de rate limit registrado"
        
        # Verifica se houve bloqueios registrados
        blocked_samples = list(metrics["rate_limit_blocked"].samples)
        assert any(
            sample.value > 0
            for sample in blocked_samples
            if sample.labels["route"] == "/test"
        ), "Nenhum bloqueio de rate limit registrado"
        
    except TimeoutError:
        logger.error("Timeout ao testar rate limit")
        pytest.fail("Timeout ao testar rate limit")
    except Exception as e:
        logger.error(f"Erro no teste de rate limit: {e}")
        pytest.fail(f"Erro no teste de rate limit: {e}")

@pytest.mark.asyncio
async def test_metrics_integration_security(client):
    """
    Testa a integração das métricas de segurança
    """
    try:
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
        
        # Aguarda propagação das métricas
        await asyncio.sleep(0.2)  # Aumentado para dar mais tempo
        
        # Verifica se as métricas foram registradas
        metrics = {
            metric.name: metric
            for metric in security_registry.collect()
            if metric.name in [
                "xss_attempts",
                "csrf_attempts",
                "unauthorized_access",
                "suspicious_ip_activity"
            ]
        }
        
        # Verifica métricas de XSS
        assert "xss_attempts" in metrics, "Métrica de XSS não encontrada"
        samples = list(metrics["xss_attempts"].samples)
        assert any(
            sample.value > 0
            for sample in samples
            if sample.labels["path"] == "/test"
        ), "Nenhuma tentativa de XSS registrada"
        
        # Verifica métricas de CSRF
        assert "csrf_attempts" in metrics, "Métrica de CSRF não encontrada"
        samples = list(metrics["csrf_attempts"].samples)
        assert any(
            sample.value > 0
            for sample in samples
            if sample.labels["path"] == "/test"
        ), "Nenhuma tentativa de CSRF registrada"
        
        # Verifica métricas de acesso não autorizado
        assert "unauthorized_access" in metrics, "Métrica de acesso não autorizado não encontrada"
        samples = list(metrics["unauthorized_access"].samples)
        assert any(
            sample.value > 0
            for sample in samples
            if sample.labels["path"] == "/test"
        ), "Nenhum acesso não autorizado registrado"
        
        # Verifica métricas de atividade suspeita
        assert "suspicious_ip_activity" in metrics, "Métrica de atividade suspeita não encontrada"
        samples = list(metrics["suspicious_ip_activity"].samples)
        assert len(samples) > 0, "Nenhuma atividade suspeita registrada"
        
        # Verifica se há registros para diferentes IPs
        ips_registrados = {
            sample.labels["ip"]
            for sample in samples
            if sample.labels["activity_type"] == "multiple_requests"
        }
        assert len(ips_registrados) > 1, f"Atividade suspeita não registrada para múltiplos IPs. IPs registrados: {ips_registrados}"
        
    except Exception as e:
        logger.error(f"Erro no teste de segurança: {e}")
        pytest.fail(f"Erro no teste de segurança: {e}")

@pytest.mark.asyncio
async def test_metrics_integration_suspicious_activity(client):
    """
    Testa a integração das métricas de atividade suspeita
    """
    try:
        # Simula atividade suspeita com múltiplos IPs
        headers = [
            {"X-Forwarded-For": f"192.168.1.{i}"}
            for i in range(10)
        ]
        
        # Faz requisições com diferentes IPs
        for i, header in enumerate(headers):
            response = client.get("/test", headers=header)
            assert response.status_code == 200
            logger.info(f"Request {i+1} com IP {header['X-Forwarded-For']}: status={response.status_code}")
        
        # Aguarda propagação das métricas
        await asyncio.sleep(0.1)
        
        # Verifica se as métricas foram registradas
        metrics = {
            metric.name: metric
            for metric in security_registry.collect()
            if metric.name == "suspicious_ip_activity"
        }
        
        # Verifica métricas de atividade suspeita
        assert "suspicious_ip_activity" in metrics, "Métrica de atividade suspeita não encontrada"
        samples = list(metrics["suspicious_ip_activity"].samples)
        assert len(samples) > 0, "Nenhuma atividade suspeita registrada"
        
        # Verifica se há registros para diferentes IPs
        ips = {
            sample.labels["ip"]
            for sample in samples
            if sample.labels["activity_type"] == "multiple_requests"
        }
        assert len(ips) > 1, "Atividade suspeita não registrada para múltiplos IPs"
        
    except Exception as e:
        logger.error(f"Erro no teste de atividade suspeita: {e}")
        pytest.fail(f"Erro no teste de atividade suspeita: {e}")

@pytest.mark.asyncio
async def test_metrics_integration_latency_distribution(client):
    """
    Testa a distribuição de latência das requisições
    """
    try:
        async with asyncio.timeout(15):
            # Faz várias requisições com delays variáveis
            for i in range(10):
                response = client.get("/test")
                assert response.status_code == 200
                logger.info(f"Request {i+1}: status={response.status_code}")
                # Delay variável baseado no índice
                await asyncio.sleep(0.05 * (i % 3 + 1))
        
        # Aguarda propagação das métricas
        await asyncio.sleep(0.1)
        
        metrics = {
            metric.name: metric
            for metric in security_registry.collect()
            if metric.name == "request_latency_seconds"
        }
        
        assert "request_latency_seconds" in metrics, "Métrica de latência não encontrada"
        samples = list(metrics["request_latency_seconds"].samples)
        
        # Verifica distribuição nos buckets
        buckets = [
            sample.value
            for sample in samples
            if sample.labels["path"] == "/test"
            and "_bucket" in sample.name
        ]
        assert len(buckets) > 0, "Nenhum bucket de latência encontrado"
        assert any(value > 0 for value in buckets), "Nenhuma latência registrada"
        
    except TimeoutError:
        logger.error("Timeout ao testar distribuição de latência")
        pytest.fail("Timeout ao testar distribuição de latência")
    except Exception as e:
        logger.error(f"Erro no teste de distribuição de latência: {e}")
        pytest.fail(f"Erro no teste de distribuição de latência: {e}") 