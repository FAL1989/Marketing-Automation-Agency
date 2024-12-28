from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
import structlog
import time
from pythonjsonlogger import jsonlogger
import logging
import sys

# Configuração do structlog
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Configuração do logging padrão
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(jsonlogger.JsonFormatter())
root_logger = logging.getLogger()
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = structlog.get_logger()

class ProviderMetricsCollector:
    def __init__(self):
        self._requests = {}
        self._errors = {}
        self._durations = {}
        self._hits = {}
        self._misses = {}
    
    def record_request(self, provider: str):
        self._requests[provider] = self._requests.get(provider, 0) + 1
    
    def record_error(self, provider: str, error_type: str):
        key = (provider, error_type)
        self._errors[key] = self._errors.get(key, 0) + 1
    
    def record_duration(self, provider: str, duration: float):
        if provider not in self._durations:
            self._durations[provider] = []
        self._durations[provider].append(duration)
    
    def record_cache_hit(self, provider: str):
        self._hits[provider] = self._hits.get(provider, 0) + 1
    
    def record_cache_miss(self, provider: str):
        self._misses[provider] = self._misses.get(provider, 0) + 1
    
    def get_stats(self, provider: str) -> Dict[str, float]:
        total_requests = self._requests.get(provider, 0)
        total_errors = sum(
            count for (p, _), count in self._errors.items()
            if p == provider
        )
        
        hits = self._hits.get(provider, 0)
        misses = self._misses.get(provider, 0)
        total_cache = hits + misses
        cache_hit_rate = (hits / total_cache) if total_cache > 0 else 0
        
        durations = self._durations.get(provider, [])
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "cache_hit_rate": cache_hit_rate,
            "avg_duration": avg_duration
        }

class MonitoringService:
    def __init__(self):
        self.registry = CollectorRegistry()
        self.metrics_collector = ProviderMetricsCollector()
        
        # Métricas de requisições
        self.generation_requests = Counter(
            'ai_generation_requests_total',
            'Total de requisições de geração por provedor',
            ['provider'],
            registry=self.registry
        )
        
        self.generation_errors = Counter(
            'ai_generation_errors_total',
            'Total de erros de geração por provedor e tipo',
            ['provider', 'error_type'],
            registry=self.registry
        )
        
        self.generation_duration = Histogram(
            'ai_generation_duration_seconds',
            'Duração das requisições de geração',
            ['provider'],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
            registry=self.registry
        )
        
        # Métricas de cache
        self.cache_hits = Counter(
            'ai_cache_hits_total',
            'Total de hits no cache',
            ['provider'],
            registry=self.registry
        )
        
        self.cache_misses = Counter(
            'ai_cache_misses_total',
            'Total de misses no cache',
            ['provider'],
            registry=self.registry
        )
        
        # Métricas de custos
        self.token_usage = Counter(
            'ai_token_usage_total',
            'Total de tokens utilizados',
            ['provider', 'model'],
            registry=self.registry
        )
        
        self.estimated_cost = Counter(
            'ai_estimated_cost_total',
            'Custo estimado total em USD',
            ['provider', 'model'],
            registry=self.registry
        )
        
        # Métricas de fallback
        self.fallback_attempts = Counter(
            'ai_fallback_attempts_total',
            'Total de tentativas de fallback',
            ['from_provider', 'to_provider'],
            registry=self.registry
        )
        
        self.fallback_success = Counter(
            'ai_fallback_success_total',
            'Total de fallbacks bem-sucedidos',
            ['from_provider', 'to_provider'],
            registry=self.registry
        )
        
        # Métricas de qualidade
        self.content_quality = Histogram(
            'ai_content_quality_score',
            'Score de qualidade do conteúdo gerado',
            ['provider', 'model'],
            buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
            registry=self.registry
        )
        
        # Métricas de sistema
        self.system_load = Gauge(
            'ai_system_load',
            'Carga do sistema de geração',
            ['component'],
            registry=self.registry
        )
    
    async def record_generation_attempt(
        self,
        provider: str,
        model: str,
        start_time: float,
        success: bool,
        error_type: str = None,
        token_count: int = 0,
        cost: float = 0.0
    ):
        """
        Registra uma tentativa de geração de conteúdo.
        """
        duration = time.time() - start_time
        
        # Atualiza métricas do Prometheus
        self.generation_requests.labels(provider=provider).inc()
        self.generation_duration.labels(provider=provider).observe(duration)
        
        # Atualiza coletor personalizado
        self.metrics_collector.record_request(provider)
        self.metrics_collector.record_duration(provider, duration)
        
        if not success and error_type:
            self.generation_errors.labels(
                provider=provider,
                error_type=error_type
            ).inc()
            self.metrics_collector.record_error(provider, error_type)
        
        if token_count > 0:
            self.token_usage.labels(
                provider=provider,
                model=model
            ).inc(token_count)
            
            self.estimated_cost.labels(
                provider=provider,
                model=model
            ).inc(cost)
        
        log_data = {
            "provider": provider,
            "model": model,
            "duration": duration,
            "success": success,
            "token_count": token_count,
            "cost": cost
        }
        
        if error_type:
            log_data["error_type"] = error_type
            
        if success:
            logger.info("generation_completed", **log_data)
        else:
            logger.error("generation_failed", **log_data)
    
    async def record_cache_event(self, provider: str, hit: bool):
        """Registra eventos de cache"""
        if hit:
            self.cache_hits.labels(provider=provider).inc()
            self.metrics_collector.record_cache_hit(provider)
        else:
            self.cache_misses.labels(provider=provider).inc()
            self.metrics_collector.record_cache_miss(provider)
    
    async def record_fallback(
        self,
        from_provider: str,
        to_provider: str,
        success: bool
    ):
        """Registra eventos de fallback entre provedores"""
        self.fallback_attempts.labels(
            from_provider=from_provider,
            to_provider=to_provider
        ).inc()
        
        if success:
            self.fallback_success.labels(
                from_provider=from_provider,
                to_provider=to_provider
            ).inc()
    
    async def record_content_quality(
        self,
        provider: str,
        model: str,
        quality_score: float
    ):
        """Registra métricas de qualidade do conteúdo"""
        self.content_quality.labels(
            provider=provider,
            model=model
        ).observe(quality_score)
    
    async def update_system_load(self, component: str, load: float):
        """Atualiza métricas de carga do sistema"""
        self.system_load.labels(component=component).set(load)
    
    def get_provider_stats(self, provider: str) -> Dict[str, Any]:
        """
        Retorna estatísticas agregadas para um provedor específico.
        Usa o coletor personalizado para evitar acesso direto às métricas do Prometheus.
        """
        return self.metrics_collector.get_stats(provider)
    
    def get_metrics(self) -> bytes:
        """
        Retorna todas as métricas no formato do Prometheus.
        Útil para endpoints de métricas.
        """
        return generate_latest(self.registry) 