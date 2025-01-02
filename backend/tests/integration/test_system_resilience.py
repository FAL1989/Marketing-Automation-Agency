import pytest
from fastapi.testclient import TestClient
from app.core.redis import redis_manager
from app.services.rate_limiter import TokenBucketRateLimiter
from app.core.security import create_access_token
from app.core.config import settings
import asyncio
import time
import random

@pytest.fixture
async def redis_client():
    """Fixture que fornece um cliente Redis limpo para testes"""
    client = await redis_manager.get_client('rate_limit')
    await client.flushdb()
    return client

@pytest.mark.asyncio
async def test_redis_connection_resilience(test_client, redis_client):
    """Testa a resiliência do sistema quando o Redis falha"""
    # Configura o token de acesso
    access_token = create_access_token(data={"sub": "test@example.com"})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Faz algumas requisições com Redis funcionando
    for _ in range(3):
        response = test_client.get(
            f"{settings.API_V1_STR}/protected/resource",
            headers=headers
        )
        assert response.status_code == 200
    
    # Força uma falha no Redis
    await redis_client.close()
    
    # Verifica se o sistema continua funcionando com fallback local
    for _ in range(3):
        response = test_client.get(
            f"{settings.API_V1_STR}/protected/resource",
            headers=headers
        )
        assert response.status_code == 200
    
    # Reconecta o Redis
    await redis_manager.initialize()
    
    # Verifica se volta a usar Redis
    response = test_client.get(
        f"{settings.API_V1_STR}/protected/resource",
        headers=headers
    )
    assert response.status_code == 200
    assert "X-Rate-Limit-Remaining" in response.headers

@pytest.mark.asyncio
async def test_concurrent_requests_resilience(test_client):
    """Testa a resiliência do sistema sob carga concorrente"""
    # Prepara múltiplos tokens de acesso
    tokens = [
        create_access_token(data={"sub": f"user{i}@example.com"})
        for i in range(10)
    ]
    
    async def make_request(token):
        headers = {"Authorization": f"Bearer {token}"}
        async with test_client as client:
            for _ in range(5):
                response = await client.get(
                    f"{settings.API_V1_STR}/protected/resource",
                    headers=headers
                )
                assert response.status_code in [200, 429]
                await asyncio.sleep(random.uniform(0.1, 0.3))
    
    # Executa requisições concorrentes
    tasks = [make_request(token) for token in tokens]
    await asyncio.gather(*tasks)

@pytest.mark.asyncio
async def test_rate_limit_recovery_resilience(test_client, redis_client):
    """Testa a resiliência do rate limit após falhas"""
    access_token = create_access_token(data={"sub": "test@example.com"})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Excede o rate limit
    responses = []
    for _ in range(settings.RATE_LIMIT_PER_MINUTE + 1):
        response = test_client.get(
            f"{settings.API_V1_STR}/protected/resource",
            headers=headers
        )
        responses.append(response.status_code)
    
    assert 429 in responses
    
    # Força uma falha no Redis
    await redis_client.close()
    
    # Espera o tempo de janela
    await asyncio.sleep(settings.RATE_LIMIT_WINDOW)
    
    # Reconecta o Redis
    await redis_manager.initialize()
    
    # Verifica se o rate limit foi resetado corretamente
    response = test_client.get(
        f"{settings.API_V1_STR}/protected/resource",
        headers=headers
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_system_degradation_resilience(test_client, redis_client):
    """Testa a resiliência do sistema em condições degradadas"""
    access_token = create_access_token(data={"sub": "test@example.com"})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async def simulate_degraded_conditions():
        # Simula latência alta no Redis
        await asyncio.sleep(1)
        return True
    
    # Patch o Redis para simular degradação
    redis_client.ping = simulate_degraded_conditions
    
    # Faz requisições sob condições degradadas
    start_time = time.time()
    response = test_client.get(
        f"{settings.API_V1_STR}/protected/resource",
        headers=headers
    )
    end_time = time.time()
    
    # Verifica se o sistema ainda funciona, mesmo que mais lento
    assert response.status_code == 200
    assert end_time - start_time < settings.REQUEST_TIMEOUT  # Não deve exceder o timeout

@pytest.mark.asyncio
async def test_mfa_system_resilience(test_client, redis_client):
    """Testa a resiliência do sistema MFA"""
    access_token = create_access_token(data={"sub": "test@example.com"})
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
            response = test_client.post(
                f"{settings.API_V1_STR}/auth/mfa/verify",
                headers=client_headers,
                json={"code": "000000"}
            )
            assert response.status_code in [401, 429]
    
    # Força falha no Redis
    await redis_client.close()
    
    # Verifica se o fallback local funciona
    response = test_client.post(
        f"{settings.API_V1_STR}/auth/mfa/verify",
        headers=headers,
        json={"code": "000000"}
    )
    assert response.status_code in [401, 429]
    
    # Reconecta o Redis
    await redis_manager.initialize() 