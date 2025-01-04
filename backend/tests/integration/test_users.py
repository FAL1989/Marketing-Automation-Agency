import pytest
import pytest_asyncio
from httpx import AsyncClient
from datetime import timedelta, timezone
from typing import Dict, Any, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token
from app.core.config import settings
from app.main import app
from app.models.user import User

pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture
async def test_user(test_client: AsyncClient, db_session: AsyncSession) -> Dict[str, Any]:
    """Create a test user for authentication."""
    user_data = {
        "email": "test@example.com",
        "password": "test123",
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False
    }
    
    response = await test_client.post(f"{settings.API_V1_STR}/users", json=user_data)
    assert response.status_code == 201
    result = response.json()
    await db_session.commit()
    return result

@pytest_asyncio.fixture
async def auth_headers(test_user: Dict[str, Any]) -> Dict[str, str]:
    """Create authentication headers for testing."""
    access_token = create_access_token(
        subject=test_user["email"],
        expires_delta=timedelta(minutes=30)
    )
    return {"Authorization": f"Bearer {access_token}"}

@pytest_asyncio.fixture
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

async def test_create_user(test_client: AsyncClient, db_session: AsyncSession) -> None:
    """Test user creation with all required fields."""
    user_data = {
        "email": "test_create@example.com",
        "password": "testpassword123",  # Longer password for security
        "full_name": "Test Create User",
        "is_active": True,
        "is_superuser": False
    }
    
    # First, verify we can create a user with all required fields
    response = await test_client.post(f"{settings.API_V1_STR}/users", json=user_data)
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.content}")
    assert response.status_code == 201
    result = response.json()
    
    # Verify all fields are present and match
    assert "id" in result
    assert result["email"] == user_data["email"]
    assert result["full_name"] == user_data["full_name"]
    assert result["is_active"] == user_data["is_active"]
    assert result["is_superuser"] == user_data["is_superuser"]
    
    # Verify we can't create a duplicate user
    response = await test_client.post(f"{settings.API_V1_STR}/users", json=user_data)
    assert response.status_code == 400
    response_json = response.json()
    assert "Email already registered" in response_json["detail"]
    
    await db_session.commit()

async def test_get_user(test_client: AsyncClient, db_session: AsyncSession, auth_headers: Dict[str, str], test_user: Dict[str, Any]) -> None:
    """Test user retrieval."""
    # Get the created user
    response = await test_client.get(
        f"{settings.API_V1_STR}/users/{test_user['id']}", 
        headers=auth_headers
    )
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == test_user["id"]
    assert result["email"] == test_user["email"]
    assert result["full_name"] == test_user["full_name"]

async def test_update_user(test_client: AsyncClient, db_session: AsyncSession, auth_headers: Dict[str, str], test_user: Dict[str, Any]) -> None:
    """Test user update."""
    # Update the user
    update_data = {
        "full_name": "Updated Test User"
    }
    response = await test_client.put(
        f"{settings.API_V1_STR}/users/{test_user['id']}", 
        json=update_data, 
        headers=auth_headers
    )
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == test_user["id"]
    assert result["full_name"] == update_data["full_name"]

async def test_delete_user(test_client: AsyncClient, db_session: AsyncSession, auth_headers: Dict[str, str], test_user: Dict[str, Any]) -> None:
    """Test user deletion."""
    # Delete the user
    response = await test_client.delete(
        f"{settings.API_V1_STR}/users/{test_user['id']}", 
        headers=auth_headers
    )
    assert response.status_code == 204
    
    # Verify the user was deleted
    get_response = await test_client.get(
        f"{settings.API_V1_STR}/users/{test_user['id']}", 
        headers=auth_headers
    )
    assert get_response.status_code == 404

async def test_list_users(test_client: AsyncClient, db_session: AsyncSession, auth_headers: Dict[str, str], test_user: Dict[str, Any]) -> None:
    """Test user listing."""
    # Create additional users
    users = [
        {
            "email": f"test_list{i}@example.com",
            "password": "test123",
            "full_name": f"Test User {i}",
            "is_active": True,
            "is_superuser": False
        }
        for i in range(3)
    ]
    
    for user_data in users:
        response = await test_client.post(f"{settings.API_V1_STR}/users", json=user_data)
        assert response.status_code == 201
    await db_session.commit()
    
    # List users
    response = await test_client.get(
        f"{settings.API_V1_STR}/users", 
        headers=auth_headers
    )
    assert response.status_code == 200
    result = response.json()
    assert len(result) >= 4  # test_user + 3 additional users
    assert all(user["email"] in [u["email"] for u in result] for user in users)

async def test_user_me(test_client: AsyncClient, db_session: AsyncSession, test_user: Dict[str, Any]) -> None:
    """Test user me endpoint."""
    # Login
    login_data = {
        "username": test_user["email"],
        "password": "test123"
    }
    login_response = await test_client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Get logged in user data
    response = await test_client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["email"] == test_user["email"]
    assert result["full_name"] == test_user["full_name"]

async def test_user_validation(test_client: AsyncClient) -> None:
    """Test user data validation."""
    # Test invalid email
    invalid_email_data = {
        "email": "invalid-email",
        "password": "test123",
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False
    }
    response = await test_client.post(f"{settings.API_V1_STR}/users", json=invalid_email_data)
    assert response.status_code == 422
    
    # Test short password
    short_password_data = {
        "email": "test@example.com",
        "password": "123",
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False
    }
    response = await test_client.post(f"{settings.API_V1_STR}/users", json=short_password_data)
    assert response.status_code == 422
    
    # Test empty name
    empty_name_data = {
        "email": "test@example.com",
        "password": "test123",
        "full_name": "",
        "is_active": True,
        "is_superuser": False
    }
    response = await test_client.post(f"{settings.API_V1_STR}/users", json=empty_name_data)
    assert response.status_code == 422 