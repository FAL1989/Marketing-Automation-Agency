import pytest
from fastapi.testclient import TestClient
import asyncio
from redis.asyncio import Redis
from app.core.monitoring import MonitoringService
from app.core.redis import redis_manager, get_redis
from app.core.config import settings
from app.services.rate_limiter import TokenBucketRateLimiter
import time
from asyncio import TimeoutError
import socket
import logging
from app.main import app

client = TestClient(app)

@pytest.fixture
async def redis():
    await redis_manager.initialize()
    redis_client = await redis_manager.get_redis()
    try:
        yield redis_client
    finally:
        await redis_manager.close()

@pytest.mark.asyncio
async def test_mfa_rate_limit_basic(redis):
    """Testa o rate limit básico do MFA"""
    # Configura rate limiter
    monitoring = MonitoringService()
    rate_limiter = TokenBucketRateLimiter(monitoring)
    
    # Tenta verificação MFA múltiplas vezes
    for _ in range(settings.RATE_LIMIT_PER_MINUTE + 1):
        response = client.post(
            "/auth/mfa/verify",
            json={"code": "123456"}
        )
    
    # Última tentativa deve ser bloqueada
    assert response.status_code == 429
    result = response.json()
    assert "detail" in result
    assert "Too many requests" in result["detail"]

@pytest.mark.asyncio
async def test_mfa_rate_limit_window_reset(redis):
    """Testa o reset da janela de rate limit do MFA"""
    monitoring = MonitoringService()
    rate_limiter = TokenBucketRateLimiter(monitoring)
    
    # Excede o rate limit
    for _ in range(settings.RATE_LIMIT_PER_MINUTE + 1):
        response = client.post(
            "/auth/mfa/verify",
            json={"code": "123456"}
        )
    
    # Espera a janela resetar
    await asyncio.sleep(settings.RATE_LIMIT_WINDOW)
    
    # Tenta novamente
    response = client.post(
        "/auth/mfa/verify",
        json={"code": "123456"}
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_mfa_rate_limit_multiple_users(redis):
    """Testa o rate limit do MFA para múltiplos usuários"""
    monitoring = MonitoringService()
    rate_limiter = TokenBucketRateLimiter(monitoring)
    
    # Testa com diferentes usuários
    users = ["user1@example.com", "user2@example.com"]
    
    for user in users:
        # Deve permitir tentativas para cada usuário
        for _ in range(settings.RATE_LIMIT_PER_MINUTE):
            response = client.post(
                "/auth/mfa/verify",
                json={"code": "123456", "email": user}
            )
            assert response.status_code == 200
        
        # Próxima tentativa deve ser bloqueada
        response = client.post(
            "/auth/mfa/verify",
            json={"code": "123456", "email": user}
        )
        assert response.status_code == 429

@pytest.mark.asyncio
async def test_mfa_rate_limit_burst(redis):
    """Testa o comportamento de burst do rate limit do MFA"""
    monitoring = MonitoringService()
    rate_limiter = TokenBucketRateLimiter(monitoring)
    
    # Tenta burst de requisições
    responses = []
    for _ in range(settings.RATE_LIMIT_BURST):
        response = client.post(
            "/auth/mfa/verify",
            json={"code": "123456"}
        )
        responses.append(response.status_code)
    
    # Verifica que o burst foi permitido
    assert all(status == 200 for status in responses)
    
    # Próxima tentativa deve ser bloqueada
    response = client.post(
        "/auth/mfa/verify",
        json={"code": "123456"}
    )
    assert response.status_code == 429

@pytest.mark.asyncio
async def test_mfa_rate_limit_cleanup(redis):
    """Testa a limpeza de dados do rate limit do MFA"""
    monitoring = MonitoringService()
    rate_limiter = TokenBucketRateLimiter(monitoring)
    
    # Excede o rate limit
    for _ in range(settings.RATE_LIMIT_PER_MINUTE + 1):
        response = client.post(
            "/auth/mfa/verify",
            json={"code": "123456"}
        )
    
    # Espera o tempo de limpeza
    await asyncio.sleep(settings.RATE_LIMIT_CLEANUP_INTERVAL)
    
    # Verifica se os dados foram limpos
    response = client.post(
        "/auth/mfa/verify",
        json={"code": "123456"}
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_mfa_rate_limit_metrics(redis):
    """Testa as métricas do rate limit do MFA"""
    monitoring = MonitoringService()
    rate_limiter = TokenBucketRateLimiter(monitoring)
    
    # Gera algumas tentativas
    for _ in range(settings.RATE_LIMIT_PER_MINUTE + 1):
        response = client.post(
            "/auth/mfa/verify",
            json={"code": "123456"}
        )
    
    # Verifica métricas
    metrics = await monitoring.get_metrics()
    assert metrics["rate_limits"]["mfa_attempts"] > 0
    assert metrics["rate_limits"]["mfa_blocks"] > 0 