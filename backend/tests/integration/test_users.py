import pytest
from fastapi.testclient import TestClient
import asyncio
from redis.asyncio import Redis
from app.core.monitoring import MonitoringService
from app.core.redis import redis_manager, get_redis
from app.core.config import settings
from app.core.security import create_access_token
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
async def test_create_user(redis):
    """Testa a criação de usuário"""
    user_data = {
        "email": "test@example.com",
        "password": "test123",
        "full_name": "Test User"
    }
    
    response = client.post("/users", json=user_data)
    assert response.status_code == 201
    result = response.json()
    assert "id" in result
    assert result["email"] == user_data["email"]
    assert result["full_name"] == user_data["full_name"]

@pytest.mark.asyncio
async def test_get_user(redis):
    """Testa a obtenção de usuário"""
    # Primeiro cria um usuário
    user_data = {
        "email": "test@example.com",
        "password": "test123",
        "full_name": "Test User"
    }
    create_response = client.post("/users", json=user_data)
    user_id = create_response.json()["id"]
    
    # Obtém o usuário criado
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == user_id
    assert result["email"] == user_data["email"]
    assert result["full_name"] == user_data["full_name"]

@pytest.mark.asyncio
async def test_update_user(redis):
    """Testa a atualização de usuário"""
    # Primeiro cria um usuário
    user_data = {
        "email": "test@example.com",
        "password": "test123",
        "full_name": "Test User"
    }
    create_response = client.post("/users", json=user_data)
    user_id = create_response.json()["id"]
    
    # Atualiza o usuário
    update_data = {
        "full_name": "Updated Test User"
    }
    response = client.put(f"/users/{user_id}", json=update_data)
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == user_id
    assert result["full_name"] == update_data["full_name"]

@pytest.mark.asyncio
async def test_delete_user(redis):
    """Testa a deleção de usuário"""
    # Primeiro cria um usuário
    user_data = {
        "email": "test@example.com",
        "password": "test123",
        "full_name": "Test User"
    }
    create_response = client.post("/users", json=user_data)
    user_id = create_response.json()["id"]
    
    # Deleta o usuário
    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 204
    
    # Verifica se o usuário foi deletado
    get_response = client.get(f"/users/{user_id}")
    assert get_response.status_code == 404

@pytest.mark.asyncio
async def test_list_users(redis):
    """Testa a listagem de usuários"""
    # Cria alguns usuários
    users = [
        {
            "email": f"test{i}@example.com",
            "password": "test123",
            "full_name": f"Test User {i}"
        }
        for i in range(3)
    ]
    
    for user_data in users:
        client.post("/users", json=user_data)
    
    # Lista os usuários
    response = client.get("/users")
    assert response.status_code == 200
    result = response.json()
    assert len(result) >= 3
    assert all(user["email"] in [u["email"] for u in result] for user in users)

@pytest.mark.asyncio
async def test_user_me(redis):
    """Testa o endpoint /me"""
    # Primeiro cria um usuário
    user_data = {
        "email": "test@example.com",
        "password": "test123",
        "full_name": "Test User"
    }
    client.post("/users", json=user_data)
    
    # Faz login
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    login_response = client.post("/auth/login", json=login_data)
    token = login_response.json()["access_token"]
    
    # Obtém dados do usuário logado
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["email"] == user_data["email"]
    assert result["full_name"] == user_data["full_name"]

@pytest.mark.asyncio
async def test_user_validation(redis):
    """Testa a validação de dados do usuário"""
    # Testa email inválido
    invalid_email = {
        "email": "invalid-email",
        "password": "test123",
        "full_name": "Test User"
    }
    response = client.post("/users", json=invalid_email)
    assert response.status_code == 422
    
    # Testa senha muito curta
    short_password = {
        "email": "test@example.com",
        "password": "123",
        "full_name": "Test User"
    }
    response = client.post("/users", json=short_password)
    assert response.status_code == 422
    
    # Testa nome vazio
    empty_name = {
        "email": "test@example.com",
        "password": "test123",
        "full_name": ""
    }
    response = client.post("/users", json=empty_name)
    assert response.status_code == 422 