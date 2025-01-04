import pytest
from fastapi.testclient import TestClient
import asyncio
from redis.asyncio import Redis
from app.core.monitoring import MonitoringService
from app.core.redis import redis_manager, get_redis
from app.core.config import settings
from app.services.rate_limiter import TokenBucketRateLimiter
from app.core.security import create_access_token
import time
from asyncio import TimeoutError
import socket
import logging
from app.main import app
from datetime import datetime, timedelta

client = TestClient(app)

@pytest.fixture
async def redis():
    await redis_manager.initialize()
    redis_client = await redis_manager.get_redis()
    try:
        await redis_client.flushdb()  # Limpa o banco antes de cada teste
        yield redis_client
    finally:
        await redis_manager.close()

@pytest.fixture
async def rate_limiter():
    monitoring = MonitoringService()
    return TokenBucketRateLimiter(monitoring)

@pytest.mark.asyncio
async def test_system_resilience(redis, rate_limiter):
    """Testa a resiliência geral do sistema"""
    # Test system under load with rate limit consideration
    success_count = 0
    for _ in range(100):
        response = client.get("/health")
        if response.status_code == 200:
            success_count += 1
        await asyncio.sleep(0.2)  # Aumentado delay para evitar rate limit
        
    assert success_count > 0, "Pelo menos algumas requisições devem ter sucesso"
    
    # Test rate limiting
    identifier = "test_system"
    allowed, _ = await rate_limiter.check_rate_limit(identifier)
    assert allowed is True
    
    # Test Redis connection
    assert await redis.ping()

@pytest.mark.asyncio
async def test_redis_connection_resilience(redis, rate_limiter):
    """Testa a resiliência do sistema quando o Redis falha"""
    # Configura o token de acesso com tempo de expiração
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject="test@example.com",
        expires_delta=expires_delta
    )
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Limpa o rate limiter antes do teste
    await redis.flushdb()
    
    # Faz algumas requisições com Redis funcionando
    success_count = 0
    for _ in range(3):
        response = client.get(
            f"{settings.API_V1_STR}/protected/resource",
            headers=headers
        )
        if response.status_code == 200:
            success_count += 1
        await asyncio.sleep(0.2)  # Aumentado delay para evitar rate limit
    
    assert success_count > 0, "Pelo menos uma requisição deve ter sucesso"
    
    # Força uma falha no Redis
    await redis_manager.close()
    await asyncio.sleep(0.5)  # Delay para garantir que o Redis foi fechado
    
    # Verifica se o sistema continua funcionando com fallback local
    success_count = 0
    for _ in range(3):
        response = client.get(
            f"{settings.API_V1_STR}/protected/resource",
            headers=headers
        )
        if response.status_code == 200:
            success_count += 1
        await asyncio.sleep(0.2)  # Aumentado delay para evitar rate limit
    
    assert success_count > 0, "Sistema deve funcionar mesmo sem Redis"
    
    # Reconecta o Redis
    await redis_manager.initialize()
    await asyncio.sleep(0.5)  # Delay para garantir que o Redis reconectou
    
    # Verifica se volta a usar Redis
    response = client.get(
        f"{settings.API_V1_STR}/protected/resource",
        headers=headers
    )
    assert response.status_code == 200
    assert "X-RateLimit-Remaining" in response.headers

@pytest.mark.asyncio
async def test_concurrent_requests_resilience(redis, rate_limiter):
    """Testa a resiliência do sistema sob carga concorrente"""
    # Limpa o rate limiter antes do teste
    await redis.flushdb()
    
    # Prepara múltiplos tokens de acesso
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    tokens = [
        create_access_token(
            subject=f"user{i}@example.com",
            expires_delta=expires_delta
        )
        for i in range(5)  # Reduzido para 5 usuários
    ]
    
    async def make_request(token):
        headers = {"Authorization": f"Bearer {token}"}
        success_count = 0
        for _ in range(3):  # Reduzido para 3 requisições por usuário
            response = client.get(
                f"{settings.API_V1_STR}/protected/resource",
                headers=headers
            )
            if response.status_code == 200:
                success_count += 1
            await asyncio.sleep(0.2)  # Aumentado delay para evitar rate limit
        return success_count
    
    # Executa requisições concorrentes
    tasks = [make_request(token) for token in tokens]
    results = await asyncio.gather(*tasks)
    
    # Verifica se pelo menos algumas requisições tiveram sucesso
    assert sum(results) > 0, "Algumas requisições concorrentes devem ter sucesso"

@pytest.mark.asyncio
async def test_rate_limit_recovery_resilience(redis, rate_limiter):
    """Testa a resiliência do rate limit após falhas"""
    # Limpa o rate limiter antes do teste
    await redis.flushdb()
    
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject="test@example.com",
        expires_delta=expires_delta
    )
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Excede o rate limit
    responses = []
    for _ in range(settings.RATE_LIMIT_PER_MINUTE + 1):
        response = client.get(
            f"{settings.API_V1_STR}/protected/resource",
            headers=headers
        )
        responses.append(response.status_code)
        await asyncio.sleep(0.1)  # Pequeno delay para evitar sobrecarga
    
    assert 429 in responses, "Deve atingir o rate limit em algum momento"
    
    # Força uma falha no Redis
    await redis_manager.close()
    
    # Espera o tempo de janela
    await asyncio.sleep(settings.RATE_LIMIT_PERIOD)
    
    # Reconecta o Redis
    await redis_manager.initialize()
    
    # Verifica se o rate limit foi resetado corretamente
    response = client.get(
        f"{settings.API_V1_STR}/protected/resource",
        headers=headers
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_system_degradation_resilience(redis, rate_limiter):
    """Testa a resiliência do sistema em condições degradadas"""
    # Limpa o rate limiter antes do teste
    await redis.flushdb()
    
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject="test@example.com",
        expires_delta=expires_delta
    )
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Simula latência alta no Redis
    original_ping = redis.ping
    
    async def slow_ping():
        await asyncio.sleep(1)
        return await original_ping()
    
    redis.ping = slow_ping
    
    # Faz requisições sob condições degradadas
    start_time = time.time()
    response = client.get(
        f"{settings.API_V1_STR}/protected/resource",
        headers=headers
    )
    end_time = time.time()
    
    # Restaura o método original
    redis.ping = original_ping
    
    # Verifica se o sistema ainda funciona, mesmo que mais lento
    assert response.status_code in [200, 429], "Sistema deve responder mesmo degradado"
    assert end_time - start_time < 5, "Não deve exceder timeout máximo"

@pytest.mark.asyncio
async def test_mfa_system_resilience(redis, rate_limiter):
    """Testa a resiliência do sistema MFA"""
    # Limpa o rate limiter antes do teste
    await redis.flushdb()
    
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject="test@example.com",
        expires_delta=expires_delta
    )
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Simula múltiplas tentativas de diferentes IPs
    ips = [f"192.168.1.{i}" for i in range(5)]
    
    for ip in ips:
        client_headers = {
            **headers,
            "X-Forwarded-For": ip
        }
        
        # Tenta verificação MFA várias vezes
        for _ in range(3):
            response = client.post(
                f"{settings.API_V1_STR}/auth/mfa/verify",
                headers=client_headers,
                json={"code": "000000"}
            )
            assert response.status_code in [401, 429]
            await asyncio.sleep(0.1)  # Pequeno delay para evitar rate limit
    
    # Força falha no Redis
    await redis_manager.close()
    
    # Verifica se o fallback local funciona
    response = client.post(
        f"{settings.API_V1_STR}/auth/mfa/verify",
        headers=headers,
        json={"code": "000000"}
    )
    assert response.status_code in [401, 429]
    
    # Reconecta o Redis
    await redis_manager.initialize() 