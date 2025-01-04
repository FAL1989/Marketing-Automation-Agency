from fastapi.testclient import TestClient
import pytest
from typing import AsyncGenerator
from redis.asyncio import Redis
from app.main import app
from app.core.monitoring import MonitoringService, MONITORING_REGISTRY
from app.core.redis import redis_manager
from datetime import datetime, UTC
import asyncio
import logging
from prometheus_client import CollectorRegistry

client = TestClient(app)

@pytest.fixture
async def redis() -> AsyncGenerator[Redis, None]:
    await redis_manager.initialize()
    redis_client = await redis_manager.get_redis()
    try:
        yield redis_client
    finally:
        await redis_manager.close()

@pytest.fixture
def monitoring_service() -> MonitoringService:
    """Fixture para o serviço de monitoramento"""
    registry = CollectorRegistry()
    service = MonitoringService(registry=registry)
    return service

@pytest.mark.asyncio
async def test_record_api_request(monitoring_service: MonitoringService) -> None:
    """Testa o registro de requisições da API"""
    # Record an API request
    await monitoring_service.record_api_request(
        endpoint="/test",
        method="GET",
        status=200,
        duration=0.1
    )
    
    # Get the current value of the counter
    counter = monitoring_service.api_requests.labels(
        endpoint="/test",
        method="GET",
        status=200
    )._value.get()
    
    # Verify that the counter was incremented
    assert counter == 1.0

@pytest.mark.asyncio
async def test_record_redis_operation(monitoring_service: MonitoringService) -> None:
    """Testa o registro de operações do Redis"""
    # Record a Redis operation
    await monitoring_service.record_redis_operation(
        operation="get",
        duration=0.05,
        success=True
    )
    
    # Get the current value of the counter
    counter = monitoring_service.redis_operations.labels(
        operation="get",
        status="success"
    )._value.get()
    
    # Verify that the counter was incremented
    assert counter == 1.0

@pytest.mark.asyncio
async def test_record_cache_operation(monitoring_service: MonitoringService) -> None:
    """Testa o registro de operações de cache"""
    # Record a cache hit
    await monitoring_service.record_cache_operation(hit=True)
    
    # Get the current value of the hits counter
    hits = monitoring_service.cache_hits._value.get()
    
    # Verify that the hits counter was incremented
    assert hits == 1.0
    
    # Record a cache miss
    await monitoring_service.record_cache_operation(hit=False)
    
    # Get the current value of the misses counter
    misses = monitoring_service.cache_misses._value.get()
    
    # Verify that the misses counter was incremented
    assert misses == 1.0

@pytest.mark.asyncio
async def test_record_rate_limit(monitoring_service: MonitoringService) -> None:
    """Testa o registro de rate limiting"""
    endpoint = "/test"
    current = 5
    
    # Record rate limit info
    await monitoring_service.record_rate_limit(
        endpoint=endpoint,
        current=current,
        exceeded=False
    )
    
    # Get the current value of the gauge
    gauge = monitoring_service.rate_limit_current.labels(
        endpoint=endpoint
    )._value.get()
    
    # Verify that the gauge was set correctly
    assert gauge == float(current)
    
    # Record a rate limit exceeded event
    await monitoring_service.record_rate_limit(
        endpoint=endpoint,
        current=current,
        exceeded=True
    )
    
    # Get the current value of the exceeded counter
    exceeded = monitoring_service.rate_limit_exceeded.labels(
        endpoint=endpoint
    )._value.get()
    
    # Verify that the exceeded counter was incremented
    assert exceeded == 1.0

@pytest.mark.asyncio
async def test_monitoring_system_load(monitoring_service: MonitoringService) -> None:
    """Testa o sistema de monitoramento sob carga"""
    # Generate load with multiple API requests
    tasks = []
    for _ in range(100):
        task = monitoring_service.record_api_request(
            endpoint="/test",
            method="GET",
            status=200,
            duration=0.1
        )
        tasks.append(task)
    
    # Execute all tasks
    await asyncio.gather(*tasks)
    
    # Get the current value of the counter
    counter = monitoring_service.api_requests.labels(
        endpoint="/test",
        method="GET",
        status=200
    )._value.get()
    
    # Verify that all requests were recorded
    assert counter == 100.0 