"""
Testes de integração para autenticação
"""

import pytest
from fastapi.testclient import TestClient
import asyncio
from redis.asyncio import Redis
from app.core.monitoring import MonitoringService
from app.core.redis import redis_manager, get_redis
from app.core.config import settings
import time
from asyncio import TimeoutError
import socket
import logging
from app.main import app
from datetime import datetime

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
async def test_login(redis):
    """Testa o login com credenciais válidas"""
    credentials = {
        "username": "test@example.com",
        "password": "test123"
    }
    
    response = client.post("/auth/login", json=credentials)
    assert response.status_code == 200, "Login falhou"
    result = response.json()
    assert "access_token" in result
    assert "token_type" in result
    assert result["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_credentials(redis):
    """Testa o login com credenciais inválidas"""
    credentials = {
        "username": "invalid@example.com",
        "password": "wrong"
    }
    
    response = client.post("/auth/login", json=credentials)
    assert response.status_code == 401, "Status code incorreto para credenciais inválidas"
    result = response.json()
    assert "detail" in result
    assert "Invalid credentials" in result["detail"]

@pytest.mark.asyncio
async def test_login_rate_limit(redis):
    """Testa o rate limit no login"""
    credentials = {
        "username": "test@example.com",
        "password": "test123"
    }
    
    # Tenta login múltiplas vezes
    for _ in range(settings.RATE_LIMIT_PER_MINUTE + 1):
        response = client.post("/auth/login", json=credentials)
    
    # Última tentativa deve ser bloqueada
    assert response.status_code == 429
    result = response.json()
    assert "detail" in result
    assert "Too many requests" in result["detail"]

@pytest.mark.asyncio
async def test_login_mfa_required(redis):
    """Testa o login com MFA requerido"""
    # Primeiro faz login normal
    credentials = {
        "username": "mfa@example.com",
        "password": "test123"
    }
    
    response = client.post("/auth/login", json=credentials)
    assert response.status_code == 200
    result = response.json()
    assert "mfa_required" in result
    assert result["mfa_required"] == True
    
    # Tenta verificar MFA
    mfa_code = {
        "code": "123456",
        "session_id": result["session_id"]
    }
    
    response = client.post("/auth/mfa/verify", json=mfa_code)
    assert response.status_code == 200
    result = response.json()
    assert "access_token" in result 