import pytest
import pytest_asyncio
from redis.asyncio import Redis
from prometheus_client import REGISTRY
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient
from app.core.config import settings
from app.core.redis import redis_manager
from app.monitoring.metrics_exporter import metrics_exporter
from app.main import app
from app.models.user import User
from app.core.security import get_password_hash
import asyncio
import logging

logger = logging.getLogger(__name__)

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_redis():
    """Configura o Redis para a sessão de testes"""
    try:
        await redis_manager.initialize()
        yield
    finally:
        await redis_manager.close()
        await asyncio.sleep(0.2)  # Delay para garantir limpeza

@pytest_asyncio.fixture(autouse=True)
async def clean_redis():
    """Limpa o Redis antes e depois de cada teste"""
    try:
        # Garante que o Redis está inicializado
        if not redis_manager._initialized:
            await redis_manager.initialize()
            await asyncio.sleep(0.1)  # Pequeno delay para garantir inicialização
        
        # Limpa dados antes do teste
        async with redis_manager.get_connection('rate_limit') as client:
            await client.flushall()
            await asyncio.sleep(0.1)  # Pequeno delay para garantir limpeza
        
        yield
        
    except Exception as e:
        logger.error(f"Erro ao limpar Redis: {e}")
        # Se falhou por estar em shutdown, tenta reinicializar
        if "Redis manager is shutting down" in str(e):
            try:
                await redis_manager.initialize()
                async with redis_manager.get_connection('rate_limit') as client:
                    await client.flushall()
            except Exception as reinit_error:
                logger.error(f"Erro ao reinicializar Redis: {reinit_error}")
        yield
    finally:
        try:
            # Limpa dados após o teste
            if redis_manager._initialized and not redis_manager._shutdown:
                async with redis_manager.get_connection('rate_limit') as client:
                    await client.flushall()
                    await asyncio.sleep(0.1)  # Pequeno delay para garantir limpeza
        except Exception as e:
            logger.error(f"Erro ao limpar Redis após teste: {e}")

@pytest_asyncio.fixture(autouse=True)
async def reset_metrics():
    """Reseta as métricas do Prometheus antes de cada teste"""
    try:
        # Garante que o servidor de métricas está desligado
        await metrics_exporter.shutdown()
        await asyncio.sleep(0.2)  # Delay maior para garantir liberação de recursos
        
        # Limpa métricas existentes
        collectors = list(REGISTRY._collector_to_names.keys())
        for collector in collectors:
            try:
                REGISTRY.unregister(collector)
            except Exception as e:
                logger.warning(f"Erro ao desregistrar coletor: {e}")
        
        # Aguarda um pouco antes de prosseguir
        await asyncio.sleep(0.1)
        
        yield
    except Exception as e:
        logger.error(f"Erro ao resetar métricas: {e}")
        yield
    finally:
        try:
            # Garante que o servidor está desligado após o teste
            await metrics_exporter.shutdown()
            await asyncio.sleep(0.2)  # Delay maior para garantir liberação de recursos
            
            # Verifica se ainda há coletores registrados
            collectors = list(REGISTRY._collector_to_names.keys())
            if collectors:
                logger.warning(f"Ainda existem {len(collectors)} coletores registrados após o teste")
                for collector in collectors:
                    try:
                        REGISTRY.unregister(collector)
                    except Exception as e:
                        logger.warning(f"Erro ao desregistrar coletor após teste: {e}")
        except Exception as e:
            logger.error(f"Erro ao desligar servidor de métricas após teste: {e}")

@pytest_asyncio.fixture(scope="session", autouse=True)
async def cleanup_metrics():
    """Garante limpeza final das métricas após todos os testes"""
    yield
    try:
        await metrics_exporter.shutdown()
        await asyncio.sleep(0.2)
        
        # Limpa todos os coletores
        collectors = list(REGISTRY._collector_to_names.keys())
        for collector in collectors:
            try:
                REGISTRY.unregister(collector)
            except Exception as e:
                logger.warning(f"Erro ao desregistrar coletor na limpeza final: {e}")
    except Exception as e:
        logger.error(f"Erro na limpeza final das métricas: {e}")

@pytest_asyncio.fixture
async def integration_db(db_session: AsyncSession):
    """Wrapper para db_session com limpeza específica para testes de integração"""
    try:
        yield db_session
    finally:
        await db_session.rollback()
        # Limpa todas as tabelas após cada teste
        for table in reversed(db_session.get_bind().dialect.get_table_names()):
            await db_session.execute(f'TRUNCATE TABLE {table} CASCADE')
        await db_session.commit()

@pytest.fixture
def client() -> TestClient:
    """Fornece um cliente de teste para a API"""
    return TestClient(app)

@pytest_asyncio.fixture
async def test_user(integration_db: AsyncSession) -> User:
    """Cria um usuário de teste no banco de dados"""
    try:
        logger.info("Criando usuário de teste")
        
        # Cria um novo usuário
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("testpass123"),
            is_active=True,
            is_superuser=False,
            mfa_enabled=False
        )
        
        # Adiciona e persiste no banco
        integration_db.add(user)
        await integration_db.commit()
        await integration_db.refresh(user)
        
        logger.info(f"Usuário de teste criado com ID: {user.id}")
        
        yield user
        
    except Exception as e:
        logger.error(f"Erro ao criar usuário de teste: {e}")
        raise
    finally:
        try:
            # Limpa após o teste
            await integration_db.delete(user)
            await integration_db.commit()
            logger.info("Usuário de teste removido")
        except Exception as e:
            logger.error(f"Erro ao remover usuário de teste: {e}") 

@pytest_asyncio.fixture(scope="session", autouse=True)
async def cleanup_redis():
    """Garante limpeza final do Redis após todos os testes"""
    yield
    try:
        if redis_manager._initialized and not redis_manager._shutdown:
            async with redis_manager.get_connection('rate_limit') as client:
                await client.flushall()
            await redis_manager.close()
            await asyncio.sleep(0.2)  # Delay para garantir limpeza
    except Exception as e:
        logger.error(f"Erro na limpeza final do Redis: {e}") 