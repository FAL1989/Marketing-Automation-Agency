from typing import Dict, Any
from datetime import timedelta

# Configurações de cache por rota
ROUTE_CACHE_CONFIG = {
    # Rotas públicas com alto tráfego
    "/": {
        "ttl": timedelta(hours=4).seconds,
        "max_size": 1000,
        "aggressive_caching": True
    },
    "/api/v1/health": {
        "ttl": timedelta(minutes=5).seconds,
        "max_size": 10,
        "aggressive_caching": True
    },
    "/api/v1/metrics": {
        "ttl": timedelta(minutes=1).seconds,
        "max_size": 10,
        "aggressive_caching": False
    },
    
    # Rotas de autenticação
    "/api/v1/auth/login": {
        "ttl": timedelta(minutes=30).seconds,
        "max_size": 100,
        "aggressive_caching": False
    },
    "/api/v1/auth/test": {
        "ttl": timedelta(hours=1).seconds,
        "max_size": 50,
        "aggressive_caching": True
    },
    
    # Rotas de usuário
    "/api/v1/users/me": {
        "ttl": timedelta(minutes=15).seconds,
        "max_size": 1000,
        "aggressive_caching": True
    },
    "/api/v1/users/test": {
        "ttl": timedelta(hours=1).seconds,
        "max_size": 50,
        "aggressive_caching": True
    },
    
    # Rotas de conteúdo
    "/api/v1/contents": {
        "ttl": timedelta(hours=2).seconds,
        "max_size": 5000,
        "aggressive_caching": True
    },
    "/api/v1/templates": {
        "ttl": timedelta(hours=4).seconds,
        "max_size": 1000,
        "aggressive_caching": True
    },
    
    # Rotas de monitoramento
    "/api/v1/audit": {
        "ttl": timedelta(minutes=30).seconds,
        "max_size": 500,
        "aggressive_caching": False
    }
}

# Configurações de otimização do Redis
REDIS_OPTIMIZATIONS = {
    "max_memory": "2gb",
    "maxmemory_policy": "allkeys-lru",
    "active_defrag": "yes",
    "active_defrag_threshold_lower": 10,
    "active_defrag_threshold_upper": 100,
    "active_defrag_cycle_min": 25,
    "active_defrag_cycle_max": 75,
    "maxmemory_samples": 10,
    "lfu_decay_time": 1,
    "lfu_log_factor": 10
}

# Configurações de otimização do cache local
LOCAL_CACHE_OPTIMIZATIONS = {
    "default_max_size": 2000,
    "min_access_for_cache": 3,
    "priority_weight_frequency": 0.7,
    "priority_weight_recency": 0.3,
    "cleanup_interval": 300,  # 5 minutos
    "max_memory_percent": 75
}

# Configurações do cache preditivo
PREDICTIVE_CACHE_CONFIG = {
    "enabled": True,
    "min_confidence": 0.7,
    "max_predictions": 5,
    "learning_rate": 0.1,
    "pattern_ttl": timedelta(days=7).seconds,
    "min_pattern_frequency": 3,
    "max_patterns_per_route": 100,
    "prefetch_batch_size": 5,
    "prefetch_concurrency": 3
}

# Configurações de monitoramento
MONITORING_CONFIG = {
    "metrics_enabled": True,
    "collect_detailed_stats": True,
    "stats_interval": 60,  # 1 minuto
    "alert_memory_threshold": 85,  # Percentual
    "alert_error_rate_threshold": 5,  # Percentual
    "alert_latency_threshold": 200,  # ms
    "record_access_patterns": True,
    "pattern_analysis_interval": 3600  # 1 hora
}

# Configurações de otimização automática
AUTO_OPTIMIZATION_CONFIG = {
    "enabled": True,
    "interval": timedelta(hours=1).seconds,
    "aggressive_cleanup_threshold": 90,  # Percentual de uso de memória
    "min_hit_rate_threshold": 50,  # Percentual
    "ttl_multiplier_high_traffic": 2,
    "ttl_multiplier_low_traffic": 0.5,
    "max_optimization_time": 30  # segundos
}

def get_route_config(route: str) -> Dict[str, Any]:
    """
    Retorna a configuração otimizada para uma rota específica.
    Usa configuração padrão se a rota não estiver definida.
    """
    default_config = {
        "ttl": timedelta(hours=1).seconds,
        "max_size": 1000,
        "aggressive_caching": False
    }
    
    # Tenta encontrar configuração específica
    for pattern, config in ROUTE_CACHE_CONFIG.items():
        if route.startswith(pattern):
            return config
    
    return default_config 