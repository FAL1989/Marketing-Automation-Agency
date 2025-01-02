from typing import Dict, Any
import multiprocessing
from pydantic import BaseSettings

class OptimizationSettings(BaseSettings):
    # Cache settings
    CACHE_TTL: int = 3600  # 1 hora
    CACHE_MAX_SIZE: int = 10000
    CACHE_STRATEGY: str = "lru"
    
    # Rate limiting
    RATE_LIMIT_STRATEGY: str = "token_bucket"
    RATE_LIMIT_WINDOW: int = 60  # segundos
    RATE_LIMIT_MAX_BURST: int = 50
    
    # Query optimization
    DB_POOL_SIZE: int = multiprocessing.cpu_count() * 2
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_STATEMENT_TIMEOUT: int = 30000  # ms
    
    # Performance thresholds
    MAX_REQUEST_TIME: float = 2.0  # segundos
    MAX_MEMORY_USAGE: float = 0.85  # 85% do limite
    MAX_CPU_USAGE: float = 0.80  # 80% do limite
    
    # Batch processing
    BATCH_SIZE: int = 100
    MAX_CONCURRENT_TASKS: int = multiprocessing.cpu_count() * 4
    
    class Config:
        env_prefix = "OPT_"

optimization_settings = OptimizationSettings()

# Configurações de cache por rota
ROUTE_CACHE_CONFIG: Dict[str, Dict[str, Any]] = {
    "/api/templates": {
        "ttl": 3600,  # 1 hora
        "strategy": "lru",
        "max_size": 1000
    },
    "/api/content": {
        "ttl": 1800,  # 30 minutos
        "strategy": "lfu",
        "max_size": 500
    },
    "/api/templates/public": {
        "ttl": 7200,  # 2 horas
        "strategy": "lru",
        "max_size": 2000
    },
    "/api/analytics/summary": {
        "ttl": 300,  # 5 minutos
        "strategy": "lru",
        "max_size": 100
    },
    "/api/metrics/basic": {
        "ttl": 60,  # 1 minuto
        "strategy": "lru",
        "max_size": 50
    },
    "/api/user/preferences": {
        "ttl": 1800,  # 30 minutos
        "strategy": "lru",
        "max_size": 1000
    }
}

# Configurações de rate limit por rota
ROUTE_RATE_LIMITS: Dict[str, Dict[str, Any]] = {
    "/api/generate": {
        "rate": 50,
        "burst": 20,
        "window": 60
    },
    "/api/analyze": {
        "rate": 30,
        "burst": 10,
        "window": 60
    }
}

# Query optimization hints
QUERY_HINTS: Dict[str, Dict[str, Any]] = {
    "content_search": {
        "index": "idx_content_search",
        "limit": 100,
        "prefetch": ["template", "user"]
    },
    "template_list": {
        "index": "idx_template_list",
        "limit": 50,
        "prefetch": ["category"]
    }
}

# Performance monitoring thresholds
PERFORMANCE_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "/api/templates": {
        "max_response_time": 0.5,  # 500ms
        "cache_hit_ratio": 0.8,    # 80%
        "max_db_queries": 3
    },
    "/api/content": {
        "max_response_time": 0.8,  # 800ms
        "cache_hit_ratio": 0.7,    # 70%
        "max_db_queries": 4
    },
    "/api/analytics": {
        "max_response_time": 1.0,  # 1s
        "cache_hit_ratio": 0.9,    # 90%
        "max_db_queries": 5
    }
}

# Configurações de batch processing
BATCH_CONFIG: Dict[str, Dict[str, Any]] = {
    "content_generation": {
        "max_size": 50,
        "timeout": 30,  # segundos
        "retry_delay": 5  # segundos
    },
    "analytics_processing": {
        "max_size": 100,
        "timeout": 60,  # segundos
        "retry_delay": 10  # segundos
    }
}

# Configurações de circuit breaker
CIRCUIT_BREAKER_CONFIG: Dict[str, Dict[str, Any]] = {
    "default": {
        "failure_threshold": 5,
        "reset_timeout": 60,  # segundos
        "half_open_timeout": 30  # segundos
    },
    "critical": {
        "failure_threshold": 3,
        "reset_timeout": 120,  # segundos
        "half_open_timeout": 60  # segundos
    }
} 