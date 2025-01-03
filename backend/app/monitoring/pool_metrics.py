"""
Métricas para monitoramento dos pools de conexão
"""

from prometheus_client import Counter, Gauge, Histogram
from contextlib import contextmanager
import time

# Métricas para o Pool de Conexões SQLAlchemy
db_pool_connections = Gauge(
    'db_pool_total_connections',
    'Número total de conexões no pool',
    ['pool_type']
)

db_pool_available = Gauge(
    'db_pool_available_connections',
    'Número de conexões disponíveis no pool',
    ['pool_type']
)

db_pool_overflow = Counter(
    'db_pool_overflow_total',
    'Número total de vezes que o pool entrou em overflow',
    ['pool_type']
)

db_connection_time = Histogram(
    'db_connection_time_seconds',
    'Tempo para obter uma conexão do pool',
    ['pool_type'],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

db_connection_errors = Counter(
    'db_connection_errors_total',
    'Número total de erros de conexão',
    ['pool_type', 'error_type']
)

# Métricas de retry
db_retry_attempts = Counter(
    'db_retry_attempts_total',
    'Número total de tentativas de retry',
    ['pool_type']
)

db_retry_success = Counter(
    'db_retry_success_total',
    'Número de retries bem-sucedidos',
    ['pool_type']
)

# Métricas de latência detalhada
db_query_latency = Histogram(
    'db_query_latency_seconds',
    'Latência das queries',
    ['pool_type', 'operation_type'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0)
)

# Métricas de saúde do pool
db_pool_health = Gauge(
    'db_pool_health_status',
    'Status de saúde do pool (1 = saudável, 0 = não saudável)',
    ['pool_type']
)

# Métricas para o Pool Redis
redis_pool_connections = Gauge(
    'redis_pool_total_connections',
    'Número total de conexões Redis no pool'
)

redis_pool_available = Gauge(
    'redis_pool_available_connections',
    'Número de conexões Redis disponíveis'
)

redis_connection_time = Histogram(
    'redis_connection_time_seconds',
    'Tempo para obter uma conexão Redis',
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

@contextmanager
def track_connection_time(pool_type: str):
    """Context manager para medir tempo de conexão"""
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        db_connection_time.labels(pool_type=pool_type).observe(duration)

@contextmanager
def track_query_time(pool_type: str, operation_type: str):
    """Context manager para medir tempo de query"""
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        db_query_latency.labels(
            pool_type=pool_type,
            operation_type=operation_type
        ).observe(duration)

def update_pool_metrics(engine, pool_type: str = 'sqlalchemy'):
    """Atualiza métricas do pool SQLAlchemy"""
    pool = engine.pool
    db_pool_connections.labels(pool_type=pool_type).set(pool.size())
    db_pool_available.labels(pool_type=pool_type).set(pool.available())
    
    # Verifica overflow
    if hasattr(pool, '_overflow') and pool._overflow > 0:
        db_pool_overflow.labels(pool_type=pool_type).inc()

    # Atualiza status de saúde
    try:
        if pool.available() > 0:
            db_pool_health.labels(pool_type=pool_type).set(1)
        else:
            db_pool_health.labels(pool_type=pool_type).set(0)
    except Exception:
        db_pool_health.labels(pool_type=pool_type).set(0)

async def update_redis_metrics(redis_pool):
    """Atualiza métricas do pool Redis"""
    info = await redis_pool.info()
    redis_pool_connections.set(info['connected_clients'])
    redis_pool_available.set(
        redis_pool.max_connections - info['connected_clients']
    )

def record_connection_error(pool_type: str, error_type: str):
    """Registra erros de conexão"""
    db_connection_errors.labels(
        pool_type=pool_type,
        error_type=error_type
    ).inc()

def record_retry_attempt(pool_type: str, success: bool = False):
    """Registra tentativa de retry"""
    db_retry_attempts.labels(pool_type=pool_type).inc()
    if success:
        db_retry_success.labels(pool_type=pool_type).inc()

__all__ = [
    "track_connection_time",
    "track_query_time",
    "update_pool_metrics",
    "update_redis_metrics",
    "record_connection_error",
    "record_retry_attempt",
    "db_pool_connections",
    "db_pool_available",
    "db_pool_overflow",
    "db_connection_time",
    "db_connection_errors",
    "db_retry_attempts",
    "db_retry_success",
    "db_query_latency",
    "db_pool_health",
    "redis_pool_connections",
    "redis_pool_available",
    "redis_connection_time"
] 