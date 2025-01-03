from fastapi import Request
from prometheus_client import Counter, Histogram, Gauge
import time
import logging
import psutil

# Logger configurado
logger = logging.getLogger(__name__)

# Métricas existentes
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Nova métrica para erros
ERROR_COUNT = Counter(
    'http_request_errors_total',
    'Total HTTP request errors',
    ['method', 'endpoint', 'error_type']
)

# Novas métricas
STATUS_COUNT = Counter(
    'http_requests_by_status',
    'HTTP requests by status code class',
    ['status_class']  # 2xx, 3xx, 4xx, 5xx
)

MEMORY_USAGE = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes',
    ['type']  # used, available, total
)

RESPONSE_SIZE = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint'],
    buckets=(100, 1_000, 10_000, 100_000, 1_000_000)
)

def update_memory_metrics():
    """Atualiza métricas de memória"""
    memory = psutil.virtual_memory()
    MEMORY_USAGE.labels('used').set(memory.used)
    MEMORY_USAGE.labels('available').set(memory.available)
    MEMORY_USAGE.labels('total').set(memory.total)

async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Normaliza o path para evitar explosão de cardinalidade
    path = request.url.path
    if path.startswith('/api/v1/'):
        # Remove IDs e outros parâmetros variáveis
        path_parts = path.split('/')
        normalized_parts = []
        for part in path_parts:
            # Se parece com um ID (só números), substitui por {id}
            if part.isdigit():
                normalized_parts.append('{id}')
            else:
                normalized_parts.append(part)
        path = '/'.join(normalized_parts)
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Métricas básicas
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=path,
            status=response.status_code
        ).inc()
        
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=path
        ).observe(duration)
        
        # Métricas de status
        status_class = f"{str(response.status_code)[0]}xx"
        STATUS_COUNT.labels(
            status_class=status_class
        ).inc()
        
        # Métricas de tamanho de resposta
        if hasattr(response, 'headers') and 'content-length' in response.headers:
            content_length = int(response.headers['content-length'])
            RESPONSE_SIZE.labels(
                method=request.method,
                endpoint=path
            ).observe(content_length)
        
        # Atualiza métricas de memória periodicamente
        update_memory_metrics()
        
        # Log para depuração
        if response.status_code >= 400:
            logger.warning(
                f"Request failed: {request.method} {path} - Status: {response.status_code}"
            )
            
        return response
        
    except Exception as e:
        # Registra o erro
        ERROR_COUNT.labels(
            method=request.method,
            endpoint=path,
            error_type=type(e).__name__
        ).inc()
        
        # Log do erro
        logger.error(
            f"Error processing request: {request.method} {path} - Error: {str(e)}",
            exc_info=True
        )
        
        # Re-raise para o handler de erros do FastAPI
        raise 