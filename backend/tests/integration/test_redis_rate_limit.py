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
async def test_redis_rate_limit(redis):
    """Testa o rate limit básico com Redis"""
    monitoring = MonitoringService()
    rate_limiter = TokenBucketRateLimiter(monitoring)
    
    # Test rate limiting with Redis
    identifier = "test_redis_rate_limit"
    
    # Should allow initial requests
    for _ in range(5):
        allowed, headers = await rate_limiter.check_rate_limit(identifier)
        assert allowed is True
    
    # Should block after limit
    allowed, headers = await rate_limiter.check_rate_limit(identifier)
    assert allowed is False

@pytest.mark.asyncio
async def test_redis_rate_limit_integration(redis):
    """Testa a integração do rate limit com Redis"""
    monitoring = MonitoringService()
    rate_limiter = TokenBucketRateLimiter(monitoring)
    
    # Make multiple requests
    responses = []
    for _ in range(settings.RATE_LIMIT_PER_MINUTE + 1):
        response = client.get("/test")
        responses.append(response.status_code)
    
    # Verify rate limiting
    assert 429 in responses
    assert responses.count(200) == settings.RATE_LIMIT_PER_MINUTE

@pytest.mark.asyncio
async def test_redis_fallback_mechanism(redis):
    """Testa o mecanismo de fallback quando Redis falha"""
    monitoring = MonitoringService()
    rate_limiter = TokenBucketRateLimiter(monitoring)
    
    # Test with Redis available
    allowed, headers = await rate_limiter.check_rate_limit("test_fallback")
    assert allowed is True
    
    # Force Redis failure
    await redis_manager.close()
    
    # Should still work with local fallback
    allowed, headers = await rate_limiter.check_rate_limit("test_fallback")
    assert allowed is True
    
    # Reconnect Redis
    await redis_manager.initialize()

@pytest.mark.asyncio
async def test_redis_rate_limit_recovery(redis):
    """Testa a recuperação do rate limit após janela de tempo"""
    monitoring = MonitoringService()
    rate_limiter = TokenBucketRateLimiter(monitoring)
    
    identifier = "test_recovery"
    
    # Exceed rate limit
    for _ in range(settings.RATE_LIMIT_PER_MINUTE + 1):
        allowed, _ = await rate_limiter.check_rate_limit(identifier)
    
    # Wait for window reset
    await asyncio.sleep(settings.RATE_LIMIT_WINDOW)
    
    # Should allow requests again
    allowed, headers = await rate_limiter.check_rate_limit(identifier)
    assert allowed is True

@pytest.mark.asyncio
async def test_redis_rate_limit_distributed(redis):
    """Testa o rate limit distribuído entre múltiplas instâncias"""
    monitoring = MonitoringService()
    rate_limiter1 = TokenBucketRateLimiter(monitoring)
    rate_limiter2 = TokenBucketRateLimiter(monitoring)
    
    identifier = "test_distributed"
    
    # Use rate limit from first instance
    for _ in range(settings.RATE_LIMIT_PER_MINUTE):
        allowed, _ = await rate_limiter1.check_rate_limit(identifier)
        assert allowed is True
    
    # Should be blocked on second instance
    allowed, _ = await rate_limiter2.check_rate_limit(identifier)
    assert allowed is False 