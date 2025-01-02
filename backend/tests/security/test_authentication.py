import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.core.security import create_access_token
from app.models.user import User
from app.core.config import settings

@pytest.mark.asyncio
async def test_login_success(test_client: AsyncClient, test_user: User):
    """
    Testa o login com credenciais válidas
    """
    response = await test_client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "test123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_password(test_client: AsyncClient, test_user: User):
    """
    Testa o login com senha inválida
    """
    response = await test_client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "wrong_password"
        }
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_current_user(test_client: AsyncClient, test_user: User):
    """
    Testa a obtenção do usuário atual com token válido
    """
    access_token = create_access_token(
        data={"sub": test_user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    response = await test_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email

@pytest.mark.asyncio
async def test_get_current_user_invalid_token(test_client: AsyncClient):
    """
    Testa a obtenção do usuário atual com token inválido
    """
    response = await test_client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401