import pytest
from fastapi.testclient import TestClient
from app.core.security import create_access_token, SecurityService
from app.models.user import User
from app.core.security import get_password_hash
from app.core.config import settings
from app.dependencies import auth_circuit_breaker
from datetime import datetime, timedelta, UTC
import logging
from jose import jwt

logger = logging.getLogger(__name__)

@pytest.fixture
async def reset_circuit_breaker():
    """Fixture que reseta o circuit breaker antes de cada teste"""
    auth_circuit_breaker._state = "closed"
    auth_circuit_breaker._failure_count = 0
    auth_circuit_breaker._last_failure_time = None
    auth_circuit_breaker._half_open_start = None
    yield

@pytest.fixture
def test_user(db):
    """Fixture que cria um usuário de teste"""
    # Verifica se o usuário já existe
    existing_user = db.query(User).filter(User.email == "test@example.com").first()
    if existing_user:
        logger.info(f"Usuário já existe: {existing_user.email}")
        return existing_user
    
    # Cria o usuário
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
        is_active=True,
        mfa_enabled=True,
        mfa_secret="TESTSECRET123",
        mfa_attempts=0,
        mfa_locked_until=None
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
        logger.info(f"Created test user: {user.email}")
        
        # Verifica se o usuário foi criado
        created_user = db.query(User).filter(User.email == "test@example.com").first()
        logger.info(f"Verified user exists: {created_user is not None}")
        if created_user:
            logger.info(f"User details: id={created_user.id}, email={created_user.email}, is_active={created_user.is_active}")
        else:
            logger.error("User not found after creation!")
        
        return user
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        db.rollback()
        raise

@pytest.mark.asyncio
async def test_mfa_verification_blocking_period(test_client, test_user, db, reset_circuit_breaker):
    """Testa o período de bloqueio após tentativas falhas de MFA"""
    # Verifica se o usuário existe no banco
    user = db.query(User).filter(User.email == "test@example.com").first()
    logger.info(f"Test user exists in database: {user is not None}")
    if user:
        logger.info(f"Test user details: id={user.id}, email={user.email}, is_active={user.is_active}")
    else:
        logger.error("Test user not found in database!")
        # Lista todos os usuários no banco
        all_users = db.query(User).all()
        logger.info(f"Total users in database: {len(all_users)}")
        for u in all_users:
            logger.info(f"User in db: id={u.id}, email={u.email}, is_active={u.is_active}")
    
    # Cria um token de acesso válido usando o SecurityService
    security_service = SecurityService()
    access_token = security_service.create_access_token(
        data={"sub": test_user.email, "scopes": ["me"]},
        expires_delta=timedelta(minutes=15)
    )
    headers = {"Authorization": f"Bearer {access_token}"}
    logger.info(f"Created access token: {access_token}")
    
    # Decodifica o token para log
    token_data = jwt.decode(
        access_token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )
    logger.info(f"Token data: {token_data}")
    logger.info(f"Headers: {headers}")
    
    # Testa o endpoint /users/me
    response = test_client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=headers
    )
    logger.info(f"Response status code: {response.status_code}")
    logger.info(f"Response body: {response.json() if response.status_code == 200 else response.text}")
    assert response.status_code == 200

    # Gera um código MFA inválido
    invalid_code = "000000"
    
    # Tenta verificar com código inválido múltiplas vezes
    for _ in range(3):
        response = test_client.post(
            f"{settings.API_V1_STR}/auth/mfa/verify",
            headers=headers,
            json={"code": invalid_code}
        )
        assert response.status_code == 400
        
        # Atualiza o usuário do banco
        db.refresh(test_user)
    
    # Verifica se o usuário está bloqueado
    assert test_user.mfa_attempts >= 3
    assert test_user.mfa_locked_until is not None
    assert test_user.mfa_locked_until > datetime.now(UTC)
    
    # Tenta mais uma verificação enquanto bloqueado
    response = test_client.post(
        f"{settings.API_V1_STR}/auth/mfa/verify",
        headers=headers,
        json={"code": "123456"}
    )
    assert response.status_code == 400
    assert "Código MFA inválido" in response.json()["detail"] 