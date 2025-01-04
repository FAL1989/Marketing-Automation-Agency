from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.agents.coordinator import AgentCoordinator
from app.models.monitoring import MonitoringMetric
from datetime import datetime
import asyncio
from redis.asyncio import Redis
from app.core.monitoring import MonitoringService
from app.core.redis import redis_manager, get_redis
from app.core.config import settings
import time
from asyncio import TimeoutError
import socket
import logging

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
async def test_agent_message_passing(redis):
    """Testa a passagem de mensagens entre agentes"""
    # Configura os agentes
    agent1_id = "agent1"
    agent2_id = "agent2"
    
    # Envia mensagem
    response = client.post(
        f"{settings.API_V1_STR}/agents/{agent1_id}/send",
        json={"recipient": agent2_id, "message": "Hello"}
    )
    assert response.status_code == 200
    
    # Verifica recebimento
    response = client.get(f"{settings.API_V1_STR}/agents/{agent2_id}/messages")
    assert response.status_code == 200
    messages = response.json()
    assert len(messages) > 0
    assert messages[0]["sender"] == agent1_id

@pytest.mark.asyncio
async def test_agent_broadcast(redis):
    """Testa broadcast de mensagens para múltiplos agentes"""
    # Configura os agentes
    agent_ids = ["agent1", "agent2", "agent3"]
    
    # Envia broadcast
    response = client.post(
        f"{settings.API_V1_STR}/agents/broadcast",
        json={"message": "Broadcast message"}
    )
    assert response.status_code == 200
    
    # Verifica recebimento por todos os agentes
    for agent_id in agent_ids:
        response = client.get(f"{settings.API_V1_STR}/agents/{agent_id}/messages")
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) > 0
        assert "Broadcast message" in str(messages)

@pytest.mark.asyncio
async def test_agent_context_sharing(redis):
    """Testa compartilhamento de contexto entre agentes"""
    # Configura os agentes
    agent1_id = "agent1"
    agent2_id = "agent2"
    
    # Define contexto
    context = {"task": "analysis", "data": {"key": "value"}}
    response = client.post(
        f"{settings.API_V1_STR}/agents/{agent1_id}/context",
        json=context
    )
    assert response.status_code == 200
    
    # Compartilha contexto
    response = client.post(
        f"{settings.API_V1_STR}/agents/{agent1_id}/share-context",
        json={"recipient": agent2_id}
    )
    assert response.status_code == 200
    
    # Verifica contexto compartilhado
    response = client.get(f"{settings.API_V1_STR}/agents/{agent2_id}/context")
    assert response.status_code == 200
    shared_context = response.json()
    assert shared_context["context"]["task"] == context["task"]

@pytest.mark.asyncio
async def test_agent_coordination(redis):
    """Testa coordenação entre agentes"""
    task_id = "task1"
    agent1_id = "agent1"
    agent2_id = "agent2"
    
    # Cria coordenação
    coordination = {
        "task_id": task_id,
        "participants": [agent1_id, agent2_id],
        "task_details": {
            "type": "development",
            "priority": "high",
            "deadline": "2024-12-31"
        }
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/agents/coordinate",
        json=coordination
    )
    assert response.status_code == 200
    result = response.json()
    assert result["task_id"] == task_id
    assert result["status"] == "assigned"
    assert agent1_id in result["assignments"]
    assert agent2_id in result["assignments"]
    
    # Verifica status
    response = client.get(
        f"{settings.API_V1_STR}/agents/tasks/{task_id}/status"
    )
    assert response.status_code == 200
    result = response.json()
    assert result["task_id"] == task_id
    assert result["status"] == "in_progress"
    assert result["assignments"][agent1_id]["status"] == "in_progress"
    assert result["assignments"][agent2_id]["status"] == "in_progress"

@pytest.mark.asyncio
async def test_agent_feedback_loop(redis):
    """Testa loop de feedback entre agentes"""
    agent1_id = "agent1"
    agent2_id = "agent2"
    
    # Envia feedback
    response = client.post(
        f"{settings.API_V1_STR}/agents/{agent1_id}/feedback",
        json={"recipient": agent2_id, "feedback": "Improve accuracy"}
    )
    assert response.status_code == 200
    
    # Verifica processamento do feedback
    response = client.get(f"{settings.API_V1_STR}/agents/{agent2_id}/feedback/status")
    assert response.status_code == 200
    status = response.json()
    assert status["processed"] == True

@pytest.mark.asyncio
async def test_agent_conflict_resolution(redis):
    """Testa resolução de conflitos entre agentes"""
    agent1_id = "agent1"
    agent2_id = "agent2"
    
    # Cria conflito
    conflict = {
        "type": "resource_access",
        "agents": [agent1_id, agent2_id],
        "resource": "database"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/agents/conflicts",
        json=conflict
    )
    assert response.status_code == 200
    
    # Resolve conflito
    response = client.post(
        f"{settings.API_V1_STR}/agents/conflicts/{conflict['type']}/resolve",
        json={"resolution": "time_sharing"}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["resolved"] == True

@pytest.mark.asyncio
async def test_agent_learning_feedback(redis):
    """Testa feedback de aprendizado entre agentes"""
    agent1_id = "agent1"
    agent2_id = "agent2"
    
    # Envia feedback
    feedback = {
        "recipient": agent2_id,
        "feedback": {
            "type": "performance",
            "score": 0.8,
            "comments": "Good job on task completion"
        }
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/agents/{agent1_id}/learning-feedback",
        json=feedback
    )
    assert response.status_code == 200
    result = response.json()
    assert result["feedback_applied"] == False
    
    # Verifica status
    response = client.get(
        f"{settings.API_V1_STR}/agents/{agent2_id}/learning-status"
    )
    assert response.status_code == 200
    result = response.json()
    assert result["feedback_applied"] == True
    assert result["feedback"]["sender"] == agent1_id

@pytest.mark.asyncio
async def test_agent_communication_error_handling(redis):
    """Testa tratamento de erros na comunicação entre agentes"""
    # Tenta enviar mensagem para agente inexistente
    response = client.post(
        "/agents/nonexistent/send",
        json={"message": "test"}
    )
    assert response.status_code == 400
    
    # Tenta broadcast com mensagem inválida
    response = client.post(
        "/agents/broadcast",
        json={"message": None}
    )
    assert response.status_code == 400
    
    # Verifica log de erros
    response = client.get("/agents/error-log")
    assert response.status_code == 200
    errors = response.json()
    assert len(errors) > 0

@pytest.mark.asyncio
async def test_agent_communication_performance(redis):
    """Testa performance da comunicação entre agentes"""
    # Prepara dados de teste
    num_messages = 1000
    message = {"content": "test message"}
    
    # Mede tempo de envio em massa
    start_time = time.time()
    for _ in range(num_messages):
        response = client.post(
            "/agents/agent1/send",
            json={"recipient": "agent2", "message": message}
        )
        assert response.status_code == 200
    end_time = time.time()
    
    # Verifica performance
    total_time = end_time - start_time
    messages_per_second = num_messages / total_time
    assert messages_per_second > 100  # Mínimo de 100 mensagens por segundo 