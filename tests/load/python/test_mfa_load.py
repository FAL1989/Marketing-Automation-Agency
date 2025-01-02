import pytest
import asyncio
import time
from typing import List
import logging
from fastapi.testclient import TestClient
import httpx
from httpx import AsyncClient
from redis.asyncio import Redis
import pyotp
import pytest_asyncio
from app.core.security import create_access_token, get_password_hash
from app.core.config import Settings
from app.models.user import User
from app.core.redis import redis_manager
from app.dependencies import get_db
from fastapi import FastAPI
from app.routers import api_router
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configura o logger do rate limiter também
rate_limit_logger = logging.getLogger("app.middleware.rate_limit")
rate_limit_logger.setLevel(logging.DEBUG)

def generate_totp_code(secret: str) -> str:
    """Gera um código TOTP válido para o segredo fornecido"""
    totp = pyotp.TOTP(secret)
    return totp.now()

def get_test_token(user: User) -> str:
    """Gera um token de acesso para o usuário de teste"""
    return create_access_token(
        data={"sub": user.email}
    )

@pytest.fixture
def test_app():
    """Create a clean FastAPI instance for testing"""
    app = FastAPI()
    app.include_router(api_router, prefix=settings.API_V1_STR)
    return app

@pytest_asyncio.fixture
async def client(test_app):
    """Fixture que fornece um cliente assíncrono para testes"""
    async with AsyncClient(app=test_app, base_url="http://testserver") as ac:
        yield ac

@pytest_asyncio.fixture
async def test_client(test_app, db):
    """
    Test client fixture that provides a TestClient instance for making requests to the FastAPI app.
    """
    async def override_get_db():
        try:
            yield db
        finally:
            pass
    
    # Override the get_db dependency
    test_app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=test_app, base_url="http://testserver") as client:
        yield client
    
    # Clean up
    test_app.dependency_overrides = {}

@pytest_asyncio.fixture(scope="function")
async def test_user(db: AsyncSession):
    logger.info("Iniciando fixture test_user")
    
    try:
        # Limpa usuários existentes
        await db.execute(delete(User))
        await db.commit()
        logger.info("Banco de dados limpo")
        
        # Cria usuário de teste
        user = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("testpass123"),
            is_active=True,
            mfa_enabled=True,
            mfa_secret=pyotp.random_base32(),
            mfa_attempts=0,
            mfa_locked_until=None
        )
        
        logger.info(f"Criando usuário: {user.email}")
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"ID do usuário: {user.id}")
        
        # Verifica se o usuário foi criado
        result = await db.execute(select(User).filter(User.email == "test@example.com"))
        created_user = result.scalar_one_or_none()
        if not created_user:
            raise Exception("Falha ao criar usuário de teste")
        
        logger.info(f"Usuário criado com sucesso: {created_user.email}")
        
        yield created_user
        
    except Exception as e:
        logger.error(f"Erro na fixture test_user: {e}")
        await db.rollback()
        raise
        
    finally:
        # Cleanup
        try:
            await db.execute(delete(User))
            await db.commit()
            logger.info("Usuário de teste removido")
        except Exception as e:
            logger.error(f"Erro ao limpar usuário de teste: {e}")
            await db.rollback()

@pytest_asyncio.fixture
async def redis_client():
    """Fixture que fornece um cliente Redis limpo para testes"""
    client = await redis_manager.get_client('rate_limit')
    await client.flushdb()
    yield client
    await client.aclose()  # Ensure connection is closed properly

@pytest.mark.asyncio
async def test_mfa_concurrent_load(client: AsyncClient, test_user: User, redis_client: Redis):
    """Testa carga concorrente no endpoint de verificação MFA"""
    
    # Configuração do teste
    num_users = 50  # Aumentado para 50 usuários
    attempts_per_user = 20  # Aumentado para 20 tentativas por usuário
    
    # Configura logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    # Prepara as requisições
    async def simulate_mfa_attempts(user_id: int) -> List[float]:
        response_times = []
        for _ in range(attempts_per_user):
            # Gera código MFA válido em 50% das tentativas
            code = generate_totp_code(test_user.mfa_secret) if random.random() > 0.5 else "000000"
            
            start_time = time.time()
            response = await client.post(
                "/api/v1/auth/mfa/verify",
                json={"code": code},
                headers={"Authorization": f"Bearer {get_test_token(test_user)}"}
            )
            end_time = time.time()
            
            response_times.append(end_time - start_time)
            logger.debug(
                f"MFA attempt - user_id: {user_id}, code: {code}, status: {response.status_code}, response_time: {end_time - start_time:.3f}s"
            )
            
            # Pequeno delay entre requisições
            await asyncio.sleep(0.05)  # Reduzido para 0.05s
        
        return response_times
    
    # Executa as requisições concorrentemente
    tasks = [simulate_mfa_attempts(i) for i in range(num_users)]
    all_response_times = await asyncio.gather(*tasks)
    
    # Análise dos resultados
    total_requests = num_users * attempts_per_user
    response_times = [t for user_times in all_response_times for t in user_times]
    avg_response_time = sum(response_times) / len(response_times)
    requests_per_second = total_requests / sum(response_times)
    
    # Conta requisições rate limited
    rate_limited = sum(1 for times in all_response_times for t in times if t > 1.0)
    rate_limited_percent = (rate_limited / total_requests) * 100
    
    # Logs dos resultados
    logger.info(f"Total de requisições: {total_requests}")
    logger.info(f"Requisições por segundo: {requests_per_second:.1f}")
    logger.info(f"Tempo médio de resposta: {avg_response_time:.3f}s")
    logger.info(f"Percentual de rate limit: {rate_limited_percent:.1f}%")
    
    # Assertions
    assert rate_limited_percent > 0, "Nenhuma requisição foi limitada"
    assert rate_limited_percent < 50, "Muitas requisições foram limitadas"

@pytest.mark.asyncio
async def test_mfa_sustained_load(client: AsyncClient, test_user: User, redis_client: Redis):
    """Testa carga sustentada no endpoint de verificação MFA"""
    
    # Configuração do teste
    duration = 10  # Aumentado para 10 segundos
    requests_per_second = 10  # Aumentado para 10 RPS
    
    # Configura logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    # Prepara as requisições
    async def simulate_mfa_attempts() -> List[float]:
        response_times = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            # Gera código MFA válido em 50% das tentativas
            code = generate_totp_code(test_user.mfa_secret) if random.random() > 0.5 else "000000"
            
            req_start = time.time()
            response = await client.post(
                "/api/v1/auth/mfa/verify",
                json={"code": code},
                headers={"Authorization": f"Bearer {get_test_token(test_user)}"}
            )
            req_end = time.time()
            
            response_times.append(req_end - req_start)
            logger.debug(
                f"MFA attempt - code: {code}, status: {response.status_code}, response_time: {req_end - req_start:.3f}s"
            )
            
            # Calcula delay para manter a taxa de requisições
            elapsed = time.time() - start_time
            expected_requests = elapsed * requests_per_second
            actual_requests = len(response_times)
            
            if actual_requests < expected_requests:
                await asyncio.sleep(1 / requests_per_second)
        
        return response_times
    
    # Executa o teste
    response_times = await simulate_mfa_attempts()
    
    # Análise dos resultados
    total_requests = len(response_times)
    avg_response_time = sum(response_times) / len(response_times)
    actual_rps = total_requests / duration
    
    # Conta requisições rate limited
    rate_limited = sum(1 for t in response_times if t > 1.0)
    rate_limited_percent = (rate_limited / total_requests) * 100
    
    # Logs dos resultados
    logger.info(f"Total de requisições: {total_requests}")
    logger.info(f"Requisições por segundo: {actual_rps:.1f}")
    logger.info(f"Tempo médio de resposta: {avg_response_time:.3f}s")
    logger.info(f"Percentual de rate limit: {rate_limited_percent:.1f}%")
    
    # Assertions
    assert actual_rps >= requests_per_second * 0.8, "Taxa de requisições muito baixa"
    assert rate_limited_percent > 0, "Nenhuma requisição foi limitada"
    assert rate_limited_percent < 50, "Muitas requisições foram limitadas" 