import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from app.core.redis import redis_manager
from app.services.rate_limiter import TokenBucketRateLimiter
from app.core.config import settings
import asyncio
import time

@pytest_asyncio.fixture(scope="function")
async def redis_client():
    """Fixture que fornece um cliente Redis limpo para testes"""
    async with redis_manager.get_connection('rate_limit') as client:
        await client.flushdb()  # Limpa o banco antes dos testes
        yield client

@pytest.fixture
def rate_limiter():
    """Fixture que fornece uma instância do rate limiter"""
    return TokenBucketRateLimiter(settings.REDIS_URL)

@pytest.mark.asyncio
async def test_redis_rate_limit_integration(redis_client, rate_limiter):
    """Testa a integração entre Redis e Rate Limiting"""
    test_key = "test:user:123"
    test_route = "/api/test"
    
    # Teste de limite normal
    for i in range(settings.RATE_LIMIT_PER_MINUTE):
        allowed, info = await rate_limiter.is_allowed(test_key, test_route)
        assert allowed, f"Requisição {i+1} deveria ser permitida"
        assert info['remaining'] == settings.RATE_LIMIT_PER_MINUTE - (i + 1)
    
    # Teste de limite excedido
    allowed, info = await rate_limiter.is_allowed(test_key, test_route)
    assert not allowed, "Requisição deveria ser bloqueada após exceder limite"
    assert info['remaining'] == 0

@pytest.mark.asyncio
async def test_redis_fallback_mechanism(redis_client, rate_limiter):
    """Testa o mecanismo de fallback quando Redis falha"""
    test_key = "test:user:456"
    test_route = "/api/test"
    
    # Força uma falha no Redis desconectando o cliente
    await redis_manager.close('rate_limit')
    
    # Verifica se o fallback local funciona
    allowed, info = await rate_limiter.is_allowed(test_key, test_route)
    assert allowed, "Fallback local deveria permitir a requisição"
    assert 'remaining' in info
    
    # Reconecta o Redis
    await redis_manager.initialize()

@pytest.mark.asyncio
async def test_redis_rate_limit_recovery(redis_client, rate_limiter):
    """Testa a recuperação do rate limit após o período"""
    test_key = "test:user:789"
    test_route = "/api/test"
    
    # Excede o limite
    for _ in range(settings.RATE_LIMIT_PER_MINUTE + 1):
        await rate_limiter.is_allowed(test_key, test_route)
    
    # Espera o período passar
    await asyncio.sleep(settings.RATE_LIMIT_PERIOD)
    
    # Verifica se o limite foi resetado
    allowed, info = await rate_limiter.is_allowed(test_key, test_route)
    assert allowed, "Rate limit deveria ser resetado após o período"
    assert info['remaining'] == settings.RATE_LIMIT_PER_MINUTE - 1

@pytest.mark.asyncio
async def test_redis_rate_limit_distributed(redis_client, rate_limiter):
    """Testa o rate limiting distribuído entre múltiplas instâncias"""
    test_key = "test:user:101112"
    test_route = "/api/test"
    
    # Simula duas instâncias usando o mesmo Redis
    limiter1 = TokenBucketRateLimiter(settings.REDIS_URL)
    limiter2 = TokenBucketRateLimiter(settings.REDIS_URL)
    
    # Alterna entre as instâncias
    for i in range(settings.RATE_LIMIT_PER_MINUTE):
        if i % 2 == 0:
            allowed, _ = await limiter1.is_allowed(test_key, test_route)
        else:
            allowed, _ = await limiter2.is_allowed(test_key, test_route)
        assert allowed, f"Requisição {i+1} deveria ser permitida"
    
    # Verifica se o limite é compartilhado
    allowed1, _ = await limiter1.is_allowed(test_key, test_route)
    allowed2, _ = await limiter2.is_allowed(test_key, test_route)
    assert not allowed1 and not allowed2, "Limite deveria ser compartilhado entre instâncias" 