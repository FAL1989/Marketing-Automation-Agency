import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.cache_service import CacheService
from app.core.monitoring import MonitoringService

@pytest.fixture
def monitoring_service():
    return MonitoringService()

@pytest.fixture
def cache_service(monitoring_service):
    return CacheService(monitoring_service=monitoring_service)

@pytest.mark.asyncio
async def test_compression_large_data(cache_service):
    """
    Testa compressão de dados grandes
    """
    # Prepara dados grandes
    large_data = {
        "data": "x" * 2000  # Maior que compression_min_size
    }
    
    # Mock do Redis
    mock_redis = AsyncMock()
    with patch("app.services.cache_service.get_redis", return_value=mock_redis):
        # Tenta salvar
        success = await cache_service.set("test_key", large_data)
        
        assert success is True
        mock_redis.set.assert_called_once()
        
        # Verifica se dados foram comprimidos (começa com magic number do gzip)
        saved_data = mock_redis.set.call_args[0][1]
        assert saved_data.startswith(b"\x1f\x8b")

@pytest.mark.asyncio
async def test_compression_small_data(cache_service):
    """
    Testa que dados pequenos não são comprimidos
    """
    # Prepara dados pequenos
    small_data = {
        "data": "test"  # Menor que compression_min_size
    }
    
    # Mock do Redis
    mock_redis = AsyncMock()
    with patch("app.services.cache_service.get_redis", return_value=mock_redis):
        # Tenta salvar
        success = await cache_service.set("test_key", small_data)
        
        assert success is True
        mock_redis.set.assert_called_once()
        
        # Verifica que dados não foram comprimidos
        saved_data = mock_redis.set.call_args[0][1]
        assert not saved_data.startswith(b"\x1f\x8b")

@pytest.mark.asyncio
async def test_compression_roundtrip(cache_service):
    """
    Testa ciclo completo de compressão/descompressão
    """
    # Prepara dados grandes
    test_data = {
        "data": "x" * 2000,
        "nested": {
            "field": "test",
            "number": 123
        }
    }
    
    # Mock do Redis
    mock_redis = AsyncMock()
    with patch("app.services.cache_service.get_redis", return_value=mock_redis):
        # Salva dados
        await cache_service.set("test_key", test_data)
        
        # Configura mock para retornar dados salvos
        saved_data = mock_redis.set.call_args[0][1]
        mock_redis.get.return_value = saved_data
        
        # Recupera dados
        retrieved_data = await cache_service.get("test_key")
        
        # Verifica que dados são iguais ao original
        assert retrieved_data == test_data

@pytest.mark.asyncio
async def test_compression_error_handling(cache_service):
    """
    Testa tratamento de erros na compressão
    """
    test_data = {
        "data": "test"
    }
    
    # Mock do Redis com erro
    mock_redis = AsyncMock()
    mock_redis.set.side_effect = Exception("Redis error")
    
    with patch("app.services.cache_service.get_redis", return_value=mock_redis):
        # Tenta salvar
        success = await cache_service.set("test_key", test_data)
        assert success is False

@pytest.mark.asyncio
async def test_get_stats_with_compression(cache_service):
    """
    Testa que estatísticas incluem informação de compressão
    """
    # Mock do Redis
    mock_redis = AsyncMock()
    mock_redis.info.return_value = {
        "keyspace_hits": "100",
        "keyspace_misses": "10",
        "used_memory": "1000",
        "maxmemory": "10000"
    }
    
    with patch("app.services.cache_service.get_redis", return_value=mock_redis):
        stats = await cache_service.get_stats()
        
        assert "compression_enabled" in stats
        assert isinstance(stats["compression_enabled"], bool) 