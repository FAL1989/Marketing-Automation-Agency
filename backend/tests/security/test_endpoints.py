import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.core.security import create_access_token
from app.models.user import User
from app.core.config import settings

@pytest.mark.asyncio
async def test_protected_endpoint_with_valid_token(test_client: AsyncClient, test_user: User):
    """
    Testa acesso a endpoint protegido com token válido
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
async def test_protected_endpoint_without_token(test_client: AsyncClient):
    """
    Testa acesso a endpoint protegido sem token
    """
    response = await test_client.get("/api/v1/users/me")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_protected_endpoint_with_expired_token(test_client: AsyncClient, test_user: User):
    """
    Testa acesso a endpoint protegido com token expirado
    """
    access_token = create_access_token(
        data={"sub": test_user.email},
        expires_delta=timedelta(minutes=-1)  # Token já expirado
    )
    
    response = await test_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_protected_endpoint_with_invalid_token(test_client: AsyncClient):
    """
    Testa acesso a endpoint protegido com token inválido
    """
    response = await test_client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401 