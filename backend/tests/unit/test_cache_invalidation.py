import pytest
from unittest.mock import AsyncMock, patch
from app.services.cache_service import CacheService
from app.core.monitoring import MonitoringService
from app.core.cache_dependencies import dependency_manager

@pytest.fixture
def monitoring_service():
    return MonitoringService()

@pytest.fixture
def cache_service(monitoring_service):
    return CacheService(monitoring_service=monitoring_service)

@pytest.fixture(autouse=True)
def clear_dependencies():
    """
    Limpa dependências antes de cada teste
    """
    dependency_manager.clear()
    yield
    dependency_manager.clear()

@pytest.mark.asyncio
async def test_cache_tags(cache_service):
    """
    Testa invalidação por tags
    """
    # Mock do Redis
    mock_redis = AsyncMock()
    with patch("app.services.cache_service.get_redis", return_value=mock_redis):
        # Define valores com tags
        await cache_service.set("key1", "value1", tags=["tag1", "tag2"])
        await cache_service.set("key2", "value2", tags=["tag1"])
        await cache_service.set("key3", "value3", tags=["tag2"])
        
        # Invalida por tag
        await cache_service.delete("key1", cascade=True)
        
        # Verifica chamadas de delete
        delete_calls = [call[0][0] for call in mock_redis.delete.call_args_list]
        assert len(delete_calls) == 3  # key1 + key2 + key3
        assert all(key in str(delete_calls) for key in ["key1", "key2", "key3"])

@pytest.mark.asyncio
async def test_cache_dependencies(cache_service):
    """
    Testa invalidação por dependências
    """
    # Mock do Redis
    mock_redis = AsyncMock()
    with patch("app.services.cache_service.get_redis", return_value=mock_redis):
        # Define valores com dependências
        await cache_service.set("parent", "parent_value")
        await cache_service.set("child1", "child1_value", dependencies=["parent"])
        await cache_service.set("child2", "child2_value", dependencies=["parent"])
        await cache_service.set("grandchild", "grandchild_value", dependencies=["child1"])
        
        # Invalida parent
        await cache_service.delete("parent", cascade=True)
        
        # Verifica chamadas de delete
        delete_calls = [call[0][0] for call in mock_redis.delete.call_args_list]
        assert len(delete_calls) == 4  # parent + child1 + child2 + grandchild
        assert all(key in str(delete_calls) for key in ["parent", "child1", "child2", "grandchild"])

@pytest.mark.asyncio
async def test_mixed_invalidation(cache_service):
    """
    Testa invalidação mista (tags + dependências)
    """
    # Mock do Redis
    mock_redis = AsyncMock()
    with patch("app.services.cache_service.get_redis", return_value=mock_redis):
        # Define valores com tags e dependências
        await cache_service.set("root", "root_value")
        await cache_service.set(
            "node1",
            "node1_value",
            dependencies=["root"],
            tags=["tag1"]
        )
        await cache_service.set(
            "node2",
            "node2_value",
            tags=["tag1"]
        )
        await cache_service.set(
            "leaf",
            "leaf_value",
            dependencies=["node1"]
        )
        
        # Invalida root
        await cache_service.delete("root", cascade=True)
        
        # Verifica chamadas de delete
        delete_calls = [call[0][0] for call in mock_redis.delete.call_args_list]
        assert len(delete_calls) == 4  # root + node1 + node2 + leaf
        assert all(key in str(delete_calls) for key in ["root", "node1", "node2", "leaf"])

@pytest.mark.asyncio
async def test_clear_with_dependencies(cache_service):
    """
    Testa limpeza com dependências
    """
    # Mock do Redis
    mock_redis = AsyncMock()
    mock_redis.scan.side_effect = [
        (0, [b"prefix:key1", b"prefix:key2"])
    ]
    
    with patch("app.services.cache_service.get_redis", return_value=mock_redis):
        # Define valores com dependências
        await cache_service.set("key1", "value1")
        await cache_service.set("key2", "value2", dependencies=["key1"])
        
        # Limpa cache
        await cache_service.clear()
        
        # Verifica que dependências foram removidas
        assert not dependency_manager._dependencies
        assert not dependency_manager._reverse_dependencies
        assert not dependency_manager._tag_to_keys
        assert not dependency_manager._key_to_tags

@pytest.mark.asyncio
async def test_error_handling(cache_service):
    """
    Testa tratamento de erros na invalidação
    """
    # Mock do Redis com erro
    mock_redis = AsyncMock()
    mock_redis.delete.side_effect = Exception("Redis error")
    
    with patch("app.services.cache_service.get_redis", return_value=mock_redis):
        # Define valor
        await cache_service.set("key", "value")
        
        # Tenta invalidar
        success = await cache_service.delete("key", cascade=True)
        assert not success 