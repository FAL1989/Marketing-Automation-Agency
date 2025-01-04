import pytest
import asyncio
import logging
from typing import AsyncGenerator, Dict
from httpx import AsyncClient
from fastapi import FastAPI
from ..conftest import app, client
from app.core.redis import get_redis, redis_manager
from app.core.config import settings
from app.core.monitoring import MonitoringService

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio(scope="session")

@pytest.fixture(autouse=True)
async def setup_redis():
    """Configura e limpa o Redis antes e depois dos testes"""
    try:
        # Inicializa conexão com Redis
        await redis_manager.initialize()
        redis = await redis_manager.get_redis()
        # Não precisa de await para o cliente síncrono
        redis.flushdb()  # Limpa o banco
        logger.info("Redis configurado para testes")
        
        yield
        
        # Limpa o Redis após os testes
        redis.flushdb()
        await redis_manager.close()
        logger.info("Redis limpo após testes")
        
    except Exception as e:
        logger.error(f"Erro ao configurar Redis para testes: {str(e)}")
        raise

@pytest.fixture
async def redis():
    """Fornece uma conexão Redis para os testes"""
    try:
        redis = await redis_manager.get_redis()
        redis.flushdb()  # Limpa o banco antes de cada teste
        return redis
    except Exception as e:
        logger.error(f"Erro ao obter conexão Redis: {str(e)}")
        raise

@pytest.fixture
async def monitoring_service():
    """Fornece um serviço de monitoramento para os testes"""
    return MonitoringService()

@pytest.fixture
async def test_app() -> FastAPI:
    """Fornece a aplicação FastAPI para os testes"""
    return app

@pytest.fixture
async def test_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Fornece um cliente HTTP assíncrono para os testes"""
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        yield ac 