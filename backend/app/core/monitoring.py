import logging
import time
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from app.core.config import settings

logger = logging.getLogger(__name__)

# Registro dedicado para métricas do MonitoringService
MONITORING_REGISTRY = CollectorRegistry()

def get_or_create_metric(metric_class, name, documentation, registry, **kwargs):
    """Retorna uma métrica existente ou cria uma nova"""
    try:
        return metric_class(name, documentation, registry=registry, **kwargs)
    except ValueError:
        # Se a métrica já existe, retorna a existente
        for metric in registry.collect():
            if metric.name == name:
                return next(
                    m for m in registry._names_to_collectors.values()
                    if isinstance(m, metric_class) and m._name == name
                )

class MonitoringService:
    """
    Serviço de monitoramento usando Prometheus
    """
    def __init__(self):
        # Métricas de API
        self.api_requests_total = get_or_create_metric(
            Counter,
            'api_requests_total',
            'Total de requisições à API',
            MONITORING_REGISTRY,
            labelnames=['endpoint', 'method', 'status']
        )
        
        self.api_request_duration_seconds = get_or_create_metric(
            Histogram,
            'api_request_duration_seconds',
            'Duração das requisições à API',
            MONITORING_REGISTRY,
            labelnames=['endpoint'],
            buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
        )
        
        # Métricas de Redis
        self.redis_operations_total = get_or_create_metric(
            Counter,
            'redis_operations_total',
            'Total de operações no Redis',
            MONITORING_REGISTRY,
            labelnames=['operation', 'status']
        )
        
        self.redis_operation_duration_seconds = get_or_create_metric(
            Histogram,
            'redis_operation_duration_seconds',
            'Duração das operações no Redis',
            MONITORING_REGISTRY,
            labelnames=['operation'],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25)
        )
        
        self.redis_connections = get_or_create_metric(
            Gauge,
            'redis_connections',
            'Número de conexões ativas com Redis',
            MONITORING_REGISTRY
        )
        
        self.redis_memory_usage_bytes = get_or_create_metric(
            Gauge,
            'redis_memory_usage_bytes',
            'Uso de memória do Redis em bytes',
            MONITORING_REGISTRY
        )
        
        # Métricas de cache
        self.cache_hits_total = get_or_create_metric(
            Counter,
            'cache_hits_total',
            'Total de hits no cache',
            MONITORING_REGISTRY
        )
        
        self.cache_misses_total = get_or_create_metric(
            Counter,
            'cache_misses_total',
            'Total de misses no cache',
            MONITORING_REGISTRY
        )
        
        self.cache_size = get_or_create_metric(
            Gauge,
            'cache_size',
            'Número de itens no cache',
            MONITORING_REGISTRY
        )
        
        # Métricas de rate limiting
        self.rate_limit_exceeded_total = get_or_create_metric(
            Counter,
            'rate_limit_exceeded_total',
            'Total de vezes que o rate limit foi excedido',
            MONITORING_REGISTRY,
            labelnames=['endpoint']
        )
        
        self.rate_limit_current = get_or_create_metric(
            Gauge,
            'rate_limit_current',
            'Número atual de requisições no período',
            MONITORING_REGISTRY,
            labelnames=['endpoint']
        )
    
    async def record_api_request(
        self,
        endpoint: str,
        method: str,
        status: int,
        duration: float
    ):
        """
        Registra uma requisição à API
        """
        try:
            self.api_requests_total.labels(
                endpoint=endpoint,
                method=method,
                status=status
            ).inc()
            
            self.api_request_duration_seconds.labels(
                endpoint=endpoint
            ).observe(duration)
            
        except Exception as e:
            logger.error(f"Erro ao registrar métricas de API: {str(e)}")
    
    async def record_redis_operation(
        self,
        operation: str,
        duration: float,
        success: bool = True
    ):
        """
        Registra uma operação no Redis
        """
        try:
            status = "success" if success else "error"
            self.redis_operations_total.labels(
                operation=operation,
                status=status
            ).inc()
            
            self.redis_operation_duration_seconds.labels(
                operation=operation
            ).observe(duration)
            
        except Exception as e:
            logger.error(f"Erro ao registrar métricas do Redis: {str(e)}")
    
    async def update_redis_stats(self, info: Dict[str, Any]):
        """
        Atualiza estatísticas do Redis
        """
        try:
            if "connected_clients" in info:
                self.redis_connections.set(float(info["connected_clients"]))
            
            if "used_memory" in info:
                self.redis_memory_usage_bytes.set(float(info["used_memory"]))
                
        except Exception as e:
            logger.error(f"Erro ao atualizar estatísticas do Redis: {str(e)}")
    
    async def record_cache_operation(self, hit: bool):
        """
        Registra uma operação de cache
        """
        try:
            if hit:
                self.cache_hits_total.inc()
            else:
                self.cache_misses_total.inc()
                
        except Exception as e:
            logger.error(f"Erro ao registrar operação de cache: {str(e)}")
    
    async def update_cache_size(self, size: int):
        """
        Atualiza o tamanho do cache
        """
        try:
            self.cache_size.set(float(size))
        except Exception as e:
            logger.error(f"Erro ao atualizar tamanho do cache: {str(e)}")
    
    async def record_rate_limit(self, endpoint: str, current: int, exceeded: bool = False):
        """
        Registra informações de rate limiting
        """
        try:
            if exceeded:
                self.rate_limit_exceeded_total.labels(endpoint=endpoint).inc()
            
            self.rate_limit_current.labels(endpoint=endpoint).set(float(current))
            
        except Exception as e:
            logger.error(f"Erro ao registrar rate limit: {str(e)}")
    
    async def record_api_success(self, endpoint: str, duration: float):
        """
        Registra uma requisição bem-sucedida
        """
        await self.record_api_request(endpoint, "GET", 200, duration)
    
    async def record_api_error(self, endpoint: str, status: int):
        """
        Registra uma requisição com erro
        """
        await self.record_api_request(endpoint, "GET", status, 0.0)
    
    async def record_rate_limit_success(self, endpoint: str):
        """
        Registra um sucesso no rate limit
        """
        try:
            self.api_requests_total.labels(
                endpoint=endpoint,
                method="RATE_LIMIT",
                status="success"
            ).inc()
        except Exception as e:
            logger.error(f"Erro ao registrar sucesso de rate limit: {str(e)}")
    
    async def record_rate_limit_failure(self, endpoint: str, error: str):
        """
        Registra uma falha no rate limit
        """
        try:
            self.api_requests_total.labels(
                endpoint=endpoint,
                method="RATE_LIMIT",
                status="failure"
            ).inc()
            logger.warning(f"Falha de rate limit em {endpoint}: {error}")
        except Exception as e:
            logger.error(f"Erro ao registrar falha de rate limit: {str(e)}")

async def get_system_metrics():
    """
    Coleta métricas do sistema
    """
    try:
        import psutil
        
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu": {
                "percent": cpu_percent
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            }
        }
    except Exception as e:
        logger.error(f"Erro ao coletar métricas do sistema: {str(e)}")
        return {}

async def get_application_metrics(db=None):
    """
    Coleta métricas da aplicação
    """
    try:
        metrics = {
            "api": {
                "requests": {
                    "total": 0,  # Placeholder
                    "success": 0,
                    "error": 0
                },
                "response_time": {
                    "avg": 0,  # Placeholder
                    "p95": 0,
                    "p99": 0
                }
            },
            "cache": {
                "hits": 0,  # Placeholder
                "misses": 0,
                "size": 0
            },
            "rate_limiting": {
                "exceeded": 0,  # Placeholder
                "current": 0
            }
        }
        
        return metrics
    except Exception as e:
        logger.error(f"Erro ao coletar métricas da aplicação: {str(e)}")
        return {} 