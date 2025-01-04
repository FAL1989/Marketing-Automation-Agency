from prometheus_client import Counter, Histogram, Gauge
from typing import Dict, Any
import logging
from app.services.rate_limiter import TokenBucketRateLimiter

logger = logging.getLogger(__name__)

# Métricas de API
API_REQUESTS = Counter('api_requests_total', 'Total de requisições à API', ['endpoint', 'method', 'status'])
API_LATENCY = Histogram('api_request_duration_seconds', 'Latência das requisições à API', ['endpoint'])

# Métricas de Rate Limiting
RATE_LIMIT_HITS = Counter('rate_limit_hits_total', 'Total de hits no rate limit', ['endpoint'])
RATE_LIMIT_BLOCKS = Counter('rate_limit_blocks_total', 'Total de bloqueios pelo rate limit', ['endpoint'])

# Métricas de Cache
CACHE_HITS = Counter('cache_hits_total', 'Total de hits no cache', ['cache_type'])
CACHE_MISSES = Counter('cache_misses_total', 'Total de misses no cache', ['cache_type'])

# Métricas de Banco de Dados
DB_CONNECTIONS = Gauge('db_connections_active', 'Conexões ativas com o banco de dados')
DB_ERRORS = Counter('db_errors_total', 'Total de erros de banco de dados', ['operation'])

# Métricas de Sistema
SYSTEM_MEMORY = Gauge('system_memory_bytes', 'Uso de memória do sistema')
SYSTEM_CPU = Gauge('system_cpu_usage', 'Uso de CPU do sistema')

def record_api_request(endpoint: str, method: str, status: int, duration: float):
    """
    Registra uma requisição à API
    """
    try:
        API_REQUESTS.labels(endpoint=endpoint, method=method, status=status).inc()
        API_LATENCY.labels(endpoint=endpoint).observe(duration)
    except Exception as e:
        logger.error(f"Erro ao registrar métricas de API: {e}")

def record_rate_limit(endpoint: str, blocked: bool = False):
    """
    Registra um evento de rate limiting
    """
    try:
        if blocked:
            RATE_LIMIT_BLOCKS.labels(endpoint=endpoint).inc()
        else:
            RATE_LIMIT_HITS.labels(endpoint=endpoint).inc()
    except Exception as e:
        logger.error(f"Erro ao registrar métricas de rate limit: {e}")

def record_cache_event(cache_type: str, hit: bool):
    """
    Registra um evento de cache
    """
    try:
        if hit:
            CACHE_HITS.labels(cache_type=cache_type).inc()
        else:
            CACHE_MISSES.labels(cache_type=cache_type).inc()
    except Exception as e:
        logger.error(f"Erro ao registrar métricas de cache: {e}")

def update_db_connections(connections: int):
    """
    Atualiza o número de conexões ativas com o banco
    """
    try:
        DB_CONNECTIONS.set(connections)
    except Exception as e:
        logger.error(f"Erro ao atualizar métricas de conexões: {e}")

def record_db_error(operation: str):
    """
    Registra um erro de banco de dados
    """
    try:
        DB_ERRORS.labels(operation=operation).inc()
    except Exception as e:
        logger.error(f"Erro ao registrar erro de banco: {e}")

def update_system_metrics(memory_bytes: float, cpu_usage: float):
    """
    Atualiza métricas do sistema
    """
    try:
        SYSTEM_MEMORY.set(memory_bytes)
        SYSTEM_CPU.set(cpu_usage)
    except Exception as e:
        logger.error(f"Erro ao atualizar métricas do sistema: {e}")

def get_current_metrics() -> Dict[str, Any]:
    """
    Retorna todas as métricas atuais
    """
    return {
        "api_requests": {
            "total": API_REQUESTS._value.sum(),
            "by_endpoint": dict(API_REQUESTS._metrics)
        },
        "rate_limits": {
            "hits": RATE_LIMIT_HITS._value.sum(),
            "blocks": RATE_LIMIT_BLOCKS._value.sum()
        },
        "cache": {
            "hits": CACHE_HITS._value.sum(),
            "misses": CACHE_MISSES._value.sum()
        },
        "database": {
            "connections": DB_CONNECTIONS._value,
            "errors": DB_ERRORS._value.sum()
        },
        "system": {
            "memory": SYSTEM_MEMORY._value,
            "cpu": SYSTEM_CPU._value
        }
    } 