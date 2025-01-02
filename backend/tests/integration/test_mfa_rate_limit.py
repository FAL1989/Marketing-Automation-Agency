import pytest
from pytest import mark
from fastapi.testclient import TestClient
import httpx
from app.core.redis import redis_manager
from app.services.rate_limiter import TokenBucketRateLimiter
from app.core.security import create_access_token, get_password_hash
from app.core.config import settings
from app.dependencies import get_db
import pyotp
import time
from fastapi import FastAPI
from app.models.user import User
import logging
from app.routers import api_router
import asyncio

logger = logging.getLogger(__name__)

@pytest.fixture
def test_app():
    """Create a clean FastAPI instance for testing"""
    app = FastAPI()
    app.include_router(api_router, prefix=settings.API_V1_STR)
    return app

@pytest.fixture
def test_client(test_app, db):
    """
    Test client fixture that provides a TestClient instance for making requests to the FastAPI app.
    """
    from fastapi.testclient import TestClient
    
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    # Override the get_db dependency
    test_app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(test_app) as client:
        yield client
    
    # Clean up
    test_app.dependency_overrides = {}

@pytest.fixture(scope="function")
def test_user(db):
    """Fixture que fornece um usuário de teste com MFA configurado"""
    logger.info("Iniciando fixture test_user")
    
    try:
        # Limpa usuários existentes
        db.query(User).delete()
        db.commit()
        logger.info("Banco de dados limpo")
        
        # Cria o usuário no banco
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("testpass123"),
            full_name="Test User",
            is_active=True,
            mfa_secret=pyotp.random_base32(),
            mfa_enabled=True,
            mfa_attempts=0,
            mfa_locked_until=None
        )
        
        logger.info(f"Criando usuário: {user.email}")
        db.add(user)
        db.commit()  # Confirma a transação
        db.refresh(user)  # Recarrega o usuário do banco
        logger.info(f"ID do usuário: {user.id}")
        
        # Verifica se o usuário foi criado corretamente
        created_user = db.query(User).filter(User.email == user.email).first()
        if created_user is None:
            raise Exception("Usuário não foi criado")
        if created_user.email != user.email:
            raise Exception("Email do usuário não corresponde")
        logger.info(f"Usuário verificado no banco: {created_user.email}")
        
        # Lista todos os usuários para debug
        all_users = db.query(User).all()
        logger.info(f"Usuários no banco: {[u.email for u in all_users]}")
        
        # Verifica se o usuário está ativo
        if not created_user.is_active:
            logger.error("Usuário não está ativo")
            created_user.is_active = True
            db.commit()
            db.refresh(created_user)
            logger.info("Usuário ativado")
        
        # Verifica se o MFA está configurado corretamente
        if not created_user.mfa_enabled or not created_user.mfa_secret:
            logger.error("MFA não está configurado corretamente")
            created_user.mfa_enabled = True
            created_user.mfa_secret = pyotp.random_base32()
            db.commit()
            db.refresh(created_user)
            logger.info("MFA configurado")
        
        yield created_user
        
        # Limpa o usuário após o teste
        db.query(User).delete()
        db.commit()
        logger.info("Usuário de teste removido")
        
    except Exception as e:
        logger.error(f"Erro na fixture test_user: {e}")
        db.rollback()
        raise e

@pytest.fixture
async def redis_client():
    """Fixture que fornece um cliente Redis limpo para testes"""
    async with redis_manager.get_connection('rate_limit') as client:
        await client.flushdb()
        yield client

@pytest.mark.asyncio
async def test_mfa_verification_rate_limit(test_client, test_user):
    """Testa o rate limiting nas verificações MFA"""
    logger.info("Iniciando teste de rate limiting MFA")
    
    async with redis_manager.get_connection('rate_limit') as redis_client:
        # Configura o token de acesso com todos os campos necessários
        access_token = create_access_token(
            data={
                "sub": test_user.email,
                "scopes": ["me"],
                "type": "access_token",
                "jti": test_user.email  # Identificador único do token
            }
        )
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Token gerado: {access_token}")
        logger.info(f"Headers: {headers}")
        
        # Verifica se o usuário está autenticado
        response = test_client.get(
            f"{settings.API_V1_STR}/users/me",
            headers=headers
        )
        logger.info(f"Verificação de autenticação - Status code: {response.status_code}")
        logger.info(f"Response body: {response.json() if response.status_code != 500 else 'Internal Server Error'}")
        
        assert response.status_code == 200, "Falha na autenticação inicial"
        
        # Verifica se o MFA está configurado corretamente
        assert test_user.mfa_enabled, "MFA não está habilitado"
        assert test_user.mfa_secret, "Segredo MFA não está configurado"
        
        # Gera um código MFA inválido para teste
        invalid_code = "000000"
        
        # Tenta verificar MFA múltiplas vezes
        for i in range(settings.MFA_MAX_ATTEMPTS + 1):
            logger.info(f"Tentativa {i+1} de {settings.MFA_MAX_ATTEMPTS + 1}")
            
            response = test_client.post(
                f"{settings.API_V1_STR}/auth/mfa/verify",
                headers=headers,
                json={"code": invalid_code}  # Apenas o campo code é necessário
            )
            
            logger.info(f"Tentativa {i+1}: Status code = {response.status_code}")
            try:
                response_body = response.json()
                logger.info(f"Response body: {response_body}")
            except Exception as e:
                logger.error(f"Erro ao decodificar response body: {e}")
                response_body = None
            
            if i < settings.MFA_MAX_ATTEMPTS:
                assert response.status_code == 400, f"Esperado status 400 na tentativa {i+1}, recebido {response.status_code}"
                assert response_body and "código mfa inválido" in response_body["detail"].lower(), "Mensagem de erro incorreta"
            else:
                assert response.status_code == 429, f"Esperado status 429 na tentativa {i+1}, recebido {response.status_code}"
                assert response_body and "rate limit exceeded" in response_body["detail"].lower(), "Mensagem de rate limit não encontrada"
                
        logger.info("Teste de rate limiting MFA concluído com sucesso")

@pytest.mark.asyncio
async def test_mfa_verification_blocking_period(test_client, test_user):
    """Testa o período de bloqueio após exceder tentativas MFA"""
    async with redis_manager.get_connection('rate_limit') as redis_client:
        # Configura o token de acesso com o scope necessário
        access_token = create_access_token(
            data={
                "sub": test_user.email,
                "scopes": ["me"],
                "type": "access_token",
                "jti": test_user.email
            }
        )
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Verifica se o usuário está autenticado
        response = test_client.get(
            f"{settings.API_V1_STR}/users/me",
            headers=headers
        )
        assert response.status_code == 200
        
        # Excede o limite de tentativas
        for _ in range(settings.MFA_MAX_ATTEMPTS):
            response = test_client.post(
                f"{settings.API_V1_STR}/auth/mfa/verify",
                headers=headers,
                json={"code": "000000"}
            )
        
        # Verifica se está bloqueado
        response = test_client.post(
            f"{settings.API_V1_STR}/auth/mfa/verify",
            headers=headers,
            json={"code": "000000"}
        )
        assert response.status_code == 429
        
        # Espera metade do tempo de bloqueio
        await asyncio.sleep(settings.MFA_BLOCK_DURATION / 2)
        response = test_client.post(
            f"{settings.API_V1_STR}/auth/mfa/verify",
            headers=headers,
            json={"code": "000000"}
        )
        assert response.status_code == 429
        
        # Espera o tempo de bloqueio passar
        await asyncio.sleep(settings.MFA_BLOCK_DURATION / 2)
        response = test_client.post(
            f"{settings.API_V1_STR}/auth/mfa/verify",
            headers=headers,
            json={"code": "000000"}
        )
        assert response.status_code == 400  # Volta a aceitar tentativas

@pytest.mark.asyncio
async def test_mfa_verification_success_reset(test_client, test_user):
    """Testa o reset do contador de tentativas após sucesso"""
    async with redis_manager.get_connection('rate_limit') as redis_client:
        # Configura o token de acesso com o scope necessário
        access_token = create_access_token(
            data={
                "sub": test_user.email,
                "scopes": ["me"],
                "type": "access_token",
                "jti": test_user.email
            }
        )
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Faz algumas tentativas inválidas
        for _ in range(settings.MFA_MAX_ATTEMPTS - 1):
            response = test_client.post(
                f"{settings.API_V1_STR}/auth/mfa/verify",
                headers=headers,
                json={"code": "000000"}
            )
            assert response.status_code == 400
        
        # Gera um código válido
        totp = pyotp.TOTP(test_user.mfa_secret)
        valid_code = totp.now()
        
        # Verifica com código válido
        response = test_client.post(
            f"{settings.API_V1_STR}/auth/mfa/verify",
            headers=headers,
            json={"code": valid_code}
        )
        assert response.status_code == 200
        
        # Verifica se o contador foi resetado tentando novamente com código inválido
        response = test_client.post(
            f"{settings.API_V1_STR}/auth/mfa/verify",
            headers=headers,
            json={"code": "000000"}
        )
        assert response.status_code == 400  # Deve aceitar nova tentativa

@pytest.mark.asyncio
async def test_mfa_verification_distributed_tracking(test_client, test_user):
    """Testa o tracking distribuído das tentativas MFA"""
    async with redis_manager.get_connection('rate_limit') as redis_client:
        # Configura tokens de acesso para simular diferentes sessões
        tokens = [
            create_access_token(
                data={
                    "sub": test_user.email,
                    "scopes": ["me"],
                    "type": "access_token",
                    "jti": f"{test_user.email}_{i}"
                }
            )
            for i in range(3)
        ]
        
        # Faz tentativas com diferentes tokens
        for i, token in enumerate(tokens):
            headers = {"Authorization": f"Bearer {token}"}
            
            # Faz algumas tentativas com cada token
            for _ in range((settings.MFA_MAX_ATTEMPTS // len(tokens)) + 1):
                response = test_client.post(
                    f"{settings.API_V1_STR}/auth/mfa/verify",
                    headers=headers,
                    json={"code": "000000"}
                )
                
                if response.status_code == 429:
                    break  # Rate limit atingido
                
                assert response.status_code == 400
        
        # Verifica se todos os tokens estão bloqueados
        for token in tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = test_client.post(
                f"{settings.API_V1_STR}/auth/mfa/verify",
                headers=headers,
                json={"code": "000000"}
            )
            assert response.status_code == 429 