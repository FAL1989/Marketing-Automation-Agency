from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.db.session import AsyncSessionLocal
from app.models.monitoring import MonitoringMetric
from datetime import datetime, timedelta
import json
import asyncio
from redis.asyncio import Redis
from app.core.monitoring import MonitoringService
from app.core.redis import redis_manager, get_redis
from app.core.config import settings
import time
from asyncio import TimeoutError
import socket
import logging
from sqlalchemy import select

client = TestClient(app)

async def get_monitoring_metrics(db_session):
    """Função auxiliar para obter métricas de monitoramento"""
    stmt = select(MonitoringMetric)
    result = await db_session.execute(stmt)
    return result.scalars().all()

@pytest.fixture
async def redis():
    await redis_manager.initialize()
    redis_client = await redis_manager.get_redis()
    try:
        yield redis_client
    finally:
        await redis_manager.close()

@pytest.mark.asyncio
async def test_record_metric(redis):
    """Testa o registro de métricas"""
    metric_data = {
        "type": "response_time",
        "value": 150.0,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = client.post("/monitoring/record", json=metric_data)
    assert response.status_code == 200
    result = response.json()
    assert "id" in result
    assert "recorded" in result
    assert result["recorded"] == True

@pytest.mark.asyncio
async def test_get_metrics_summary(redis):
    """Testa o resumo das métricas"""
    response = client.get("/monitoring/summary")
    assert response.status_code == 200
    summary = response.json()
    assert "system" in summary
    assert "agents" in summary
    assert "performance" in summary

@pytest.mark.asyncio
async def test_get_agent_metrics(redis):
    """Testa as métricas dos agentes"""
    # Primeiro registra algumas métricas
    metric_data = {
        "type": "response_time",
        "value": 150.0,
        "timestamp": datetime.utcnow().isoformat()
    }
    client.post("/monitoring/record", json=metric_data)
    
    response = client.get("/monitoring/agents/test-agent")
    assert response.status_code == 200
    metrics = response.json()
    assert "metrics" in metrics
    assert "history" in metrics
    assert len(metrics["history"]) > 0

@pytest.mark.asyncio
async def test_get_system_health(redis):
    """Testa a saúde do sistema"""
    response = client.get("/monitoring/health")
    assert response.status_code == 200
    health = response.json()
    assert "status" in health
    assert "components" in health
    assert "timestamp" in health

@pytest.mark.asyncio
async def test_get_performance_metrics(redis):
    """Testa as métricas de performance"""
    response = client.get("/monitoring/performance")
    assert response.status_code == 200
    performance = response.json()
    assert "cpu_usage" in performance
    assert "memory_usage" in performance
    assert "response_times" in performance

@pytest.mark.asyncio
async def test_metrics_aggregation(redis):
    """Testa a agregação de métricas"""
    monitoring = MonitoringService()
    
    # Registra múltiplas métricas
    for i in range(5):
        await monitoring.record_api_request(
            "/test",
            "GET",
            200,
            0.1 + i * 0.1
        )
    
    # Verifica agregação
    metrics = await monitoring.get_metrics()
    assert "api_requests" in metrics
    assert metrics["api_requests"]["total"] > 0
    assert metrics["api_requests"]["success_rate"] > 0

@pytest.mark.asyncio
async def test_prometheus_metrics(redis):
    """Testa as métricas do Prometheus"""
    response = client.get("/metrics")
    assert response.status_code == 200
    metrics_text = response.text
    
    # Verifica métricas esperadas
    assert "api_requests_total" in metrics_text
    assert "api_request_duration_seconds" in metrics_text
    assert "redis_operations_total" in metrics_text

@pytest.mark.asyncio
async def test_alerts_configuration(redis):
    """Testa a configuração de alertas"""
    alert_config = {
        "metric": "response_time",
        "threshold": 1000,
        "condition": "greater_than",
        "duration": "5m",
        "notification": {
            "type": "email",
            "recipients": ["admin@example.com"]
        }
    }
    
    response = client.post("/monitoring/alerts/configure", json=alert_config)
    assert response.status_code == 200
    result = response.json()
    assert "id" in result
    assert "status" in result
    assert result["status"] == "configured"

@pytest.mark.asyncio
async def test_get_active_alerts(redis):
    """Testa a obtenção de alertas ativos"""
    response = client.get("/monitoring/alerts")
    assert response.status_code == 200
    alerts = response.json()
    assert isinstance(alerts, list)
    if alerts:
        assert all(
            isinstance(alert, dict) and
            all(key in alert for key in ["id", "metric", "threshold", "status"])
            for alert in alerts
        )

@pytest.mark.asyncio
async def test_metric_data_validation(redis):
    """Testa a validação de dados das métricas"""
    # Testa com tipo de métrica inválido
    invalid_metric = {
        "type": "invalid_type",
        "value": 150.0,
        "timestamp": datetime.utcnow().isoformat()
    }
    response = client.post("/monitoring/record", json=invalid_metric)
    assert response.status_code == 422
    
    # Testa com tipo de valor inválido
    invalid_value = {
        "type": "response_time",
        "value": "not_a_number",
        "timestamp": datetime.utcnow().isoformat()
    }
    response = client.post("/monitoring/record", json=invalid_value)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_monitoring_system_load(redis):
    """Testa o sistema de monitoramento sob carga"""
    monitoring = MonitoringService()
    
    # Gera carga com múltiplas métricas
    tasks = []
    for _ in range(100):
        task = monitoring.record_api_request(
            "/test",
            "GET",
            200,
            0.1
        )
        tasks.append(task)
    
    # Executa todas as tarefas
    await asyncio.gather(*tasks)
    
    # Verifica métricas
    metrics = await monitoring.get_metrics()
    assert metrics["api_requests"]["total"] >= 100
    assert metrics["api_requests"]["success_rate"] > 0

@pytest.mark.asyncio
async def test_monitoring_metrics(db_session):
    # Create test metric
    metric = MonitoringMetric(
        metric_type="response_time",
        value=100.0,
        timestamp=datetime.utcnow()
    )
    db_session.add(metric)
    await db_session.commit()

    # Test retrieval
    metrics = await get_monitoring_metrics(db_session)
    assert len(metrics) > 0
    assert metrics[0].metric_type == "response_time"
    assert metrics[0].value == 100.0 