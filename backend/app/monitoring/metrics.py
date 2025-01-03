from prometheus_client import Counter, Histogram, Gauge, REGISTRY
from prometheus_client.core import GaugeMetricFamily
from typing import Dict, Any
import psutil

class SystemCollector:
    def collect(self):
        # CPU
        cpu_usage = psutil.cpu_percent()
        yield GaugeMetricFamily('system_cpu_usage', 'CPU usage in percent', value=cpu_usage)
        
        # Memory
        memory = psutil.virtual_memory()
        yield GaugeMetricFamily('system_memory_usage', 'Memory usage in percent', value=memory.percent)
        yield GaugeMetricFamily('system_memory_available', 'Available memory in bytes', value=memory.available)
        yield GaugeMetricFamily('system_memory_total', 'Total memory in bytes', value=memory.total)
        
        # Disk
        disk = psutil.disk_usage('/')
        yield GaugeMetricFamily('system_disk_usage', 'Disk usage in percent', value=disk.percent)
        yield GaugeMetricFamily('system_disk_free', 'Free disk space in bytes', value=disk.free)
        yield GaugeMetricFamily('system_disk_total', 'Total disk space in bytes', value=disk.total)
        
        # Network
        net = psutil.net_io_counters()
        yield GaugeMetricFamily('system_network_bytes_sent', 'Network bytes sent', value=net.bytes_sent)
        yield GaugeMetricFamily('system_network_bytes_recv', 'Network bytes received', value=net.bytes_recv)

# Registra o coletor
REGISTRY.register(SystemCollector())

class PerformanceMetrics:
    def __init__(self):
        # Latência de requisições
        self.request_latency = Histogram(
            'request_latency_seconds',
            'Request latency in seconds',
            ['method', 'endpoint'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
        )
        
        # Contadores de requisições lentas
        self.slow_requests = Counter(
            'slow_requests_total',
            'Total number of slow requests',
            ['method', 'endpoint']
        )
        
        # Cache hits/misses
        self.cache_hits = Counter(
            'cache_hits_total',
            'Total number of cache hits',
            ['cache_type']
        )
        self.cache_misses = Counter(
            'cache_misses_total',
            'Total number of cache misses',
            ['cache_type']
        )
        
        # Rate limiting
        self.rate_limit_hits = Counter(
            'rate_limit_hits_total',
            'Total number of rate limit hits',
            ['endpoint']
        )
        
        # Métricas de recursos
        self.memory_usage = Gauge(
            'memory_usage_bytes',
            'Current memory usage in bytes'
        )
        self.cpu_usage = Gauge(
            'cpu_usage_percent',
            'Current CPU usage percentage'
        )
        
        # Métricas de banco de dados
        self.db_query_duration = Histogram(
            'db_query_duration_seconds',
            'Database query duration in seconds',
            ['query_type'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0]
        )
        self.db_connections = Gauge(
            'db_connections',
            'Number of active database connections'
        )
        self.db_errors = Counter(
            'db_errors_total',
            'Total number of database errors',
            ['error_type']
        )
        
        # Métricas de batch processing
        self.batch_processing_duration = Histogram(
            'batch_processing_duration_seconds',
            'Batch processing duration in seconds',
            ['batch_type'],
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0]
        )
        self.batch_size = Histogram(
            'batch_size',
            'Number of items in batch',
            ['batch_type'],
            buckets=[10, 50, 100, 500, 1000]
        )
        
        # Circuit breaker
        self.circuit_breaker_trips = Counter(
            'circuit_breaker_trips_total',
            'Total number of circuit breaker trips',
            ['service']
        )
        self.circuit_breaker_state = Gauge(
            'circuit_breaker_state',
            'Circuit breaker state (0=closed, 1=open, 2=half-open)',
            ['service']
        )

performance_metrics = PerformanceMetrics()

def record_metric(metric_type: str, value: float, labels: Dict[str, Any] = None):
    """
    Função helper para registrar métricas com labels opcionais
    """
    if not labels:
        labels = {}
        
    if hasattr(performance_metrics, metric_type):
        metric = getattr(performance_metrics, metric_type)
        if isinstance(metric, (Counter, Gauge)):
            if labels:
                metric.labels(**labels).inc(value)
            else:
                metric.inc(value)
        elif isinstance(metric, Histogram):
            if labels:
                metric.labels(**labels).observe(value)
            else:
                metric.observe(value) 