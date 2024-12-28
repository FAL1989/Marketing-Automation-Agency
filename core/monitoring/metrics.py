from prometheus_client import Counter, Histogram, Gauge
from functools import wraps
import time
from typing import Callable
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

# Configuração de logging
logger = logging.getLogger("ai_platform")
logger.setLevel(logging.INFO)

# Handler para arquivo
log_file = "logs/ai_platform.log"
os.makedirs(os.path.dirname(log_file), exist_ok=True)
file_handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=5)
file_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)
logger.addHandler(file_handler)

# Métricas Prometheus
http_requests_total = Counter(
    'http_requests_total',
    'Total de requisições HTTP',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'Duração das requisições HTTP',
    ['method', 'endpoint']
)

active_users = Gauge(
    'active_users',
    'Número de usuários ativos'
)

ai_requests_total = Counter(
    'ai_requests_total',
    'Total de requisições aos serviços de IA',
    ['service', 'model', 'status']
)

ai_request_duration_seconds = Histogram(
    'ai_request_duration_seconds',
    'Duração das requisições aos serviços de IA',
    ['service', 'model']
)

def monitor_http_request(method: str, endpoint: str):
    """Decorator para monitorar requisições HTTP."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                response = await func(*args, **kwargs)
                status = response.status_code
            except Exception as e:
                logger.error(f"Erro na requisição {method} {endpoint}: {str(e)}")
                status = 500
                raise
            finally:
                duration = time.time() - start_time
                http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
                http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
            
            return response
        return wrapper
    return decorator

def monitor_ai_request(service: str, model: str):
    """Decorator para monitorar requisições aos serviços de IA."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                response = await func(*args, **kwargs)
                status = "success"
                logger.info(f"Requisição IA bem-sucedida: {service}/{model}")
            except Exception as e:
                status = "error"
                logger.error(f"Erro na requisição IA {service}/{model}: {str(e)}")
                raise
            finally:
                duration = time.time() - start_time
                ai_requests_total.labels(service=service, model=model, status=status).inc()
                ai_request_duration_seconds.labels(service=service, model=model).observe(duration)
            
            return response
        return wrapper
    return decorator

def log_error(error: Exception, context: dict = None):
    """Registra erros com contexto adicional."""
    error_details = {
        "timestamp": datetime.utcnow().isoformat(),
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context or {}
    }
    logger.error(f"Erro detectado: {error_details}")

def track_active_users(delta: int = 1):
    """Atualiza o contador de usuários ativos."""
    active_users.inc(delta)

def reset_metrics():
    """Reinicia todas as métricas (��til para testes)."""
    http_requests_total._metrics.clear()
    http_request_duration_seconds._metrics.clear()
    active_users._metrics.clear()
    ai_requests_total._metrics.clear()
    ai_request_duration_seconds._metrics.clear() 