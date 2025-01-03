from typing import Dict, Any
from app.core.config import settings

# Configurações de TTL por tipo de operação
CACHE_TTL_CONFIG = {
    "get_by_id": 300,        # 5 minutos
    "get_all": 180,          # 3 minutos
    "get_by_filter": 240,    # 4 minutos
    "count": 120,            # 2 minutos
    "custom_query": 300      # 5 minutos
}

# Configurações de prefixo por tipo de operação
CACHE_PREFIX_CONFIG = {
    "get_by_id": "id",
    "get_all": "all",
    "get_by_filter": "filter",
    "count": "count",
    "custom_query": "query"
}

# Configurações de invalidação de cache
CACHE_INVALIDATION_CONFIG = {
    "on_update": True,       # Invalidar cache ao atualizar
    "on_delete": True,       # Invalidar cache ao deletar
    "cascade": True          # Invalidar caches relacionados
}

# Configurações de compressão
CACHE_COMPRESSION_CONFIG = {
    "enabled": True,
    "min_size": 1024,       # Comprimir apenas dados maiores que 1KB
    "algorithm": "gzip"      # Algoritmo de compressão
}

# Configurações de performance
CACHE_PERFORMANCE_CONFIG = {
    "max_connections": settings.REDIS_MAX_CONNECTIONS,
    "connection_timeout": settings.REDIS_TIMEOUT,
    "retry_on_timeout": True,
    "max_retries": 3
}

def get_cache_config() -> Dict[str, Any]:
    """
    Retorna configuração completa do cache
    """
    return {
        "ttl": CACHE_TTL_CONFIG,
        "prefix": CACHE_PREFIX_CONFIG,
        "invalidation": CACHE_INVALIDATION_CONFIG,
        "compression": CACHE_COMPRESSION_CONFIG,
        "performance": CACHE_PERFORMANCE_CONFIG
    }

def get_cache_ttl(operation: str) -> int:
    """
    Retorna TTL para operação específica
    """
    return CACHE_TTL_CONFIG.get(operation, 300)

def get_cache_prefix(operation: str) -> str:
    """
    Retorna prefixo para operação específica
    """
    return CACHE_PREFIX_CONFIG.get(operation, "default") 