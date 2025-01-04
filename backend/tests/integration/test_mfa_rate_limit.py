import pytest
from fastapi.testclient import TestClient
import asyncio
from redis.asyncio import Redis
from typing import AsyncGenerator, Dict, Any
from app.core.monitoring import MonitoringService
from app.core.redis import redis_manager, get_redis
from app.core.config import settings
from app.services.rate_limiter import TokenBucketRateLimiter
import time
from asyncio import TimeoutError
import socket
import logging
from app.main import app
import pyotp

client = TestClient(app)

@pytest.fixture
async def redis() -> AsyncGenerator[Redis, None]:
    """Create a mock Redis client for testing"""
    from unittest.mock import AsyncMock
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = True
    yield mock_redis

@pytest.mark.asyncio
async def test_mfa_rate_limit_basic(redis: Redis, test_user: Any, client: TestClient) -> None:
    """Testa o rate limit básico do MFA"""
    # Primeiro faz login para obter o token
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "test@example.com", "password": "testpass123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Tenta verificação MFA múltiplas vezes
    headers = {"Authorization": f"Bearer {token}"}
    for _ in range(settings.RATE_LIMIT_PER_MINUTE + 1):
        response = client.post(
            f"{settings.API_V1_STR}/auth/mfa/verify",
            json={"code": "123456"},
            headers=headers
        )
    
    # Última tentativa deve ser bloqueada
    assert response.status_code == 429
    result = response.json()
    assert "detail" in result
    assert "Rate limit excedido" in result["detail"]

@pytest.mark.asyncio
async def test_mfa_rate_limit_window_reset(redis: Redis, test_user: Any, client: TestClient) -> None:
    """Testa o reset da janela de rate limit do MFA"""
    # Primeiro faz login para obter o token
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "test@example.com", "password": "testpass123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Gera um código TOTP válido
    totp = pyotp.TOTP(test_user.mfa_secret)
    
    # Faz exatamente MFA_RATE_LIMIT_PER_MINUTE requisições válidas
    headers = {"Authorization": f"Bearer {token}"}
    for _ in range(settings.MFA_RATE_LIMIT_PER_MINUTE):
        valid_code = totp.now()  # Gera um novo código para cada tentativa
        response = client.post(
            f"{settings.API_V1_STR}/auth/mfa/verify",
            json={"code": valid_code},
            headers=headers
        )
        assert response.status_code == 200  # Deve ser 200 pois estamos usando códigos válidos
    
    # Próxima tentativa deve ser bloqueada pelo rate limit
    valid_code = totp.now()
    response = client.post(
        f"{settings.API_V1_STR}/auth/mfa/verify",
        json={"code": valid_code},
        headers=headers
    )
    assert response.status_code == 429  # Rate limit excedido
    result = response.json()
    assert "Rate limit excedido" in result["detail"]
    
    # Espera a janela resetar (2 segundos para garantir)
    await asyncio.sleep(2)
    
    # Tenta novamente com um novo código válido
    valid_code = totp.now()
    response = client.post(
        f"{settings.API_V1_STR}/auth/mfa/verify",
        json={"code": valid_code},
        headers=headers
    )
    assert response.status_code == 200  # Deve passar após o reset da janela

@pytest.mark.asyncio
async def test_mfa_rate_limit_multiple_users(redis: Redis, db_session: Any, client: TestClient) -> None:
    """Testa o rate limit do MFA para múltiplos usuários"""
    from app.models.user import User
    from app.core.security import get_password_hash
    from app.core.mfa import MFAService
    
    # Criar dois usuários de teste
    users = []
    mfa_service = MFAService(db_session)
    
    for email in ["user1@example.com", "user2@example.com"]:
        user = User(
            email=email,
            hashed_password=get_password_hash("testpass123"),
            is_active=True,
            is_superuser=False,
            mfa_enabled=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Habilitar MFA para o usuário
        mfa_data = await mfa_service.enable_mfa(user)
        users.append((user, mfa_data))
    
    # Testar rate limit para cada usuário
    for user, mfa_data in users:
        # Fazer login para obter o token
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={"username": user.email, "password": "testpass123"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Gerar códigos TOTP válidos
        totp = pyotp.TOTP(user.mfa_secret)
        
        # Fazer tentativas até o limite
        for _ in range(settings.MFA_RATE_LIMIT_PER_MINUTE):
            valid_code = totp.now()
            response = client.post(
                f"{settings.API_V1_STR}/auth/mfa/verify",
                json={"code": valid_code},
                headers=headers
            )
            assert response.status_code == 200
        
        # Próxima tentativa deve ser bloqueada
        valid_code = totp.now()
        response = client.post(
            f"{settings.API_V1_STR}/auth/mfa/verify",
            json={"code": valid_code},
            headers=headers
        )
        assert response.status_code == 429
        result = response.json()
        assert "Rate limit excedido" in result["detail"]

@pytest.mark.asyncio
async def test_mfa_rate_limit_burst(redis: Redis, test_user: Any, client: TestClient) -> None:
    """Testa o comportamento de burst do rate limit do MFA"""
    # Primeiro faz login para obter o token
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "test@example.com", "password": "testpass123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Gera um código TOTP válido
    totp = pyotp.TOTP(test_user.mfa_secret)
    
    # Tenta burst de requisições
    responses = []
    for _ in range(settings.RATE_LIMIT_BURST):
        valid_code = totp.now()
        response = client.post(
            f"{settings.API_V1_STR}/auth/mfa/verify",
            json={"code": valid_code},
            headers=headers
        )
        responses.append(response.status_code)
    
    # Verifica que o burst foi permitido
    assert all(status == 200 for status in responses)
    
    # Próxima tentativa deve ser bloqueada
    valid_code = totp.now()
    response = client.post(
        f"{settings.API_V1_STR}/auth/mfa/verify",
        json={"code": valid_code},
        headers=headers
    )
    assert response.status_code == 429
    result = response.json()
    assert "Rate limit excedido" in result["detail"]

@pytest.mark.asyncio
async def test_mfa_rate_limit_cleanup(redis: Redis, test_user: Any, client: TestClient) -> None:
    """Testa a limpeza de dados do rate limit do MFA"""
    # Primeiro faz login para obter o token
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "test@example.com", "password": "testpass123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Gera um código TOTP válido
    totp = pyotp.TOTP(test_user.mfa_secret)
    
    # Faz exatamente MFA_RATE_LIMIT_PER_MINUTE requisições válidas
    for _ in range(settings.MFA_RATE_LIMIT_PER_MINUTE):
        valid_code = totp.now()
        response = client.post(
            f"{settings.API_V1_STR}/auth/mfa/verify",
            json={"code": valid_code},
            headers=headers
        )
        assert response.status_code == 200
    
    # Próxima tentativa deve ser bloqueada pelo rate limit
    valid_code = totp.now()
    response = client.post(
        f"{settings.API_V1_STR}/auth/mfa/verify",
        json={"code": valid_code},
        headers=headers
    )
    assert response.status_code == 429
    result = response.json()
    assert "Rate limit excedido" in result["detail"]
    
    # Espera a janela de rate limit resetar
    await asyncio.sleep(settings.MFA_RATE_LIMIT_WINDOW + 1)
    
    # Verifica se os dados foram limpos e uma nova tentativa é permitida
    valid_code = totp.now()
    response = client.post(
        f"{settings.API_V1_STR}/auth/mfa/verify",
        json={"code": valid_code},
        headers=headers
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_mfa_rate_limit_metrics(redis: Redis) -> None:
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