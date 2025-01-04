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
async def test_list_agents(redis):
    """Testa listagem de agentes"""
    response = client.get("/agents")
    assert response.status_code == 200
    agents = response.json()
    assert isinstance(agents, list)
    assert len(agents) > 0

@pytest.mark.asyncio
async def test_get_agent_details(redis):
    """Testa obtenção de detalhes do agente"""
    # Primeiro lista os agentes
    response = client.get("/agents")
    assert response.status_code == 200
    agents = response.json()
    
    # Pega detalhes do primeiro agente
    agent_id = agents[0]["id"]
    response = client.get(f"/agents/{agent_id}")
    assert response.status_code == 200
    agent = response.json()
    assert agent["id"] == agent_id

@pytest.mark.asyncio
async def test_agent_interactions(redis):
    """Testa interações entre agentes"""
    # Lista agentes disponíveis
    response = client.get("/agents")
    assert response.status_code == 200
    agents = response.json()
    
    # Pega dois agentes para interação
    agent1 = agents[0]
    agent2 = agents[1]
    
    # Cria uma interação
    interaction = {
        "type": "collaboration",
        "source": agent1["id"],
        "target": agent2["id"],
        "task": "code_review"
    }
    
    response = client.post("/agents/interact", json=interaction)
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"

@pytest.mark.asyncio
async def test_agent_metrics(redis):
    """Testa métricas dos agentes"""
    # Lista agentes
    response = client.get("/agents")
    assert response.status_code == 200
    agents = response.json()
    
    # Pega métricas do primeiro agente
    agent_id = agents[0]["id"]
    response = client.get(f"/agents/{agent_id}/metrics")
    assert response.status_code == 200
    metrics = response.json()
    assert "performance" in metrics
    assert "response_time" in metrics

@pytest.mark.asyncio
async def test_agent_analysis_request(redis):
    """Testa requisição de análise para agentes"""
    request_data = {
        "type": "code_analysis",
        "content": "def example(): pass",
        "language": "python"
    }
    
    response = client.post("/agents/analyze", json=request_data)
    assert response.status_code == 200
    result = response.json()
    assert "analysis" in result
    assert "suggestions" in result

@pytest.mark.asyncio
async def test_agent_collaboration(redis):
    """Testa colaboração entre agentes"""
    task = {
        "type": "code_review",
        "content": "def example(): pass",
        "requirements": ["security", "performance"]
    }
    
    response = client.post("/agents/collaborate", json=task)
    assert response.status_code == 200
    result = response.json()
    assert "reviews" in result
    assert len(result["reviews"]) >= 2

@pytest.mark.asyncio
async def test_agent_metrics_recording(redis):
    """Testa gravação de métricas dos agentes"""
    # Cria uma métrica
    metric = {
        "type": "response_time",
        "value": 150.0,
        "timestamp": datetime.utcnow()
    }
    
    response = client.post("/agents/metrics", json=metric)
    assert response.status_code == 200
    result = response.json()
    assert result["recorded"] == True

@pytest.mark.asyncio
async def test_agent_error_handling(redis):
    """Testa tratamento de erros dos agentes"""
    # Tenta análise com dados inválidos
    invalid_request = {
        "type": "invalid_type",
        "content": None
    }
    
    response = client.post("/agents/analyze", json=invalid_request)
    assert response.status_code == 422
    error = response.json()
    assert "detail" in error

@pytest.mark.asyncio
async def test_agent_performance_under_load(redis):
    """Testa performance dos agentes sob carga"""
    # Prepara múltiplas requisições
    num_requests = 50
    request_data = {
        "type": "code_analysis",
        "content": "def example(): pass",
        "language": "python"
    }
    
    # Mede tempo de resposta
    start_time = time.time()
    for _ in range(num_requests):
        response = client.post("/agents/analyze", json=request_data)
        assert response.status_code == 200
    end_time = time.time()
    
    # Verifica performance
    total_time = end_time - start_time
    requests_per_second = num_requests / total_time
    assert requests_per_second > 10  # Mínimo de 10 requisições por segundo 