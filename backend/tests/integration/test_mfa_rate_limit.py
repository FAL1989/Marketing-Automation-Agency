import pytest
import asyncio
from httpx import AsyncClient
from app.core.redis import get_redis
from app.core.monitoring import MonitoringService
from app.services.rate_limiter import RateLimiter

@pytest.mark.asyncio
async def test_mfa_rate_limit_basic(test_client: AsyncClient, redis, monitoring_service: MonitoringService):
    """Testa o rate limiting básico do MFA"""
    # Configura rate limiter
    rate_limiter = RateLimiter(
        monitoring_service=monitoring_service,
        max_requests=5,
        window_size=10
    )
    
    # Testa requisições dentro do limite
    for i in range(5):
        allowed, headers = await rate_limiter.check_rate_limit("test_user")
        assert allowed, f"Requisição {i+1} deveria ser permitida"
        assert int(headers["X-RateLimit-Remaining"]) == 4 - i
    
    # Testa bloqueio após exceder limite
    allowed, headers = await rate_limiter.check_rate_limit("test_user")
    assert not allowed, "Requisição deveria ser bloqueada após exceder limite"
    assert int(headers["X-RateLimit-Remaining"]) == 0

@pytest.mark.asyncio
async def test_mfa_rate_limit_window_reset(test_client: AsyncClient, redis, monitoring_service: MonitoringService):
    """Testa o reset da janela de rate limiting"""
    # Configura rate limiter com janela pequena para teste
    rate_limiter = RateLimiter(
        monitoring_service=monitoring_service,
        max_requests=2,
        window_size=1  # 1 segundo
    )
    
    # Usa todas as requisições disponíveis
    for _ in range(2):
        allowed, _ = await rate_limiter.check_rate_limit("test_user")
        assert allowed
    
    # Verifica bloqueio
    allowed, _ = await rate_limiter.check_rate_limit("test_user")
    assert not allowed
    
    # Aguarda reset da janela
    await asyncio.sleep(1.1)
    
    # Verifica que pode fazer requisições novamente
    allowed, headers = await rate_limiter.check_rate_limit("test_user")
    assert allowed
    assert int(headers["X-RateLimit-Remaining"]) == 1

@pytest.mark.asyncio
async def test_mfa_rate_limit_multiple_users(test_client: AsyncClient, redis, monitoring_service: MonitoringService):
    """Testa rate limiting para múltiplos usuários"""
    rate_limiter = RateLimiter(
        monitoring_service=monitoring_service,
        max_requests=3,
        window_size=10
    )
    
    # Testa limites independentes para diferentes usuários
    for user in ["user1", "user2", "user3"]:
        for i in range(3):
            allowed, headers = await rate_limiter.check_rate_limit(user)
            assert allowed, f"Requisição {i+1} para {user} deveria ser permitida"
            assert int(headers["X-RateLimit-Remaining"]) == 2 - i
        
        # Verifica bloqueio após exceder limite
        allowed, _ = await rate_limiter.check_rate_limit(user)
        assert not allowed, f"{user} deveria ser bloqueado após exceder limite"

@pytest.mark.asyncio
async def test_mfa_rate_limit_burst(test_client: AsyncClient, redis, monitoring_service: MonitoringService):
    """Testa comportamento de burst do rate limiting"""
    rate_limiter = RateLimiter(
        monitoring_service=monitoring_service,
        max_requests=5,
        window_size=10,
        burst_size=7  # Permite burst maior que o rate normal
    )
    
    # Testa burst inicial
    for i in range(7):
        allowed, headers = await rate_limiter.check_rate_limit("test_user")
        assert allowed, f"Requisição de burst {i+1} deveria ser permitida"
    
    # Verifica bloqueio após exceder burst
    allowed, _ = await rate_limiter.check_rate_limit("test_user")
    assert not allowed, "Requisição deveria ser bloqueada após exceder burst"

@pytest.mark.asyncio
async def test_mfa_rate_limit_cleanup(test_client: AsyncClient, redis, monitoring_service: MonitoringService):
    """Testa limpeza de limites"""
    rate_limiter = RateLimiter(
        monitoring_service=monitoring_service,
        max_requests=3,
        window_size=10
    )
    
    # Usa algumas requisições
    for _ in range(2):
        await rate_limiter.check_rate_limit("test_user")
    
    # Limpa limites
    await rate_limiter.clear_limits("test_user")
    
    # Verifica que o contador foi resetado
    allowed, headers = await rate_limiter.check_rate_limit("test_user")
    assert allowed
    assert int(headers["X-RateLimit-Remaining"]) == 2

@pytest.mark.asyncio
async def test_mfa_rate_limit_metrics(test_client: AsyncClient, redis, monitoring_service: MonitoringService):
    """Testa métricas do rate limiting"""
    rate_limiter = RateLimiter(
        monitoring_service=monitoring_service,
        max_requests=3,
        window_size=10
    )
    
    # Executa algumas requisições
    for _ in range(4):
        await rate_limiter.check_rate_limit("test_user")
    
    # Verifica informações dos limites
    limits = await rate_limiter.get_limits("test_user")
    assert limits["limit"] == 3
    assert limits["remaining"] == 0
    assert "reset" in limits
    assert limits["window"] == 10 