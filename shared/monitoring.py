from opentelemetry import trace, metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from typing import Dict, Any
import time

class MonitoringService:
    def __init__(self, service_name: str):
        # Configuração do recurso
        resource = Resource.create({
            "service.name": service_name
        })
        
        # Configuração de tracing
        trace_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(trace_provider)
        self.tracer = trace.get_tracer(__name__)
        
        # Configuração de métricas
        metric_reader = PrometheusMetricReader()
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(meter_provider)
        self.meter = metrics.get_meter(__name__)
        
        # Contadores e medidores comuns
        self.request_counter = self.meter.create_counter(
            "app_requests_total",
            description="Total de requisições",
            unit="1"
        )
        
        self.request_duration = self.meter.create_histogram(
            "request_duration_seconds",
            description="Duração das requisições",
            unit="s"
        )
        
        self.error_counter = self.meter.create_counter(
            "app_errors_total",
            description="Total de erros",
            unit="1"
        )
        
        self.active_users = self.meter.create_up_down_counter(
            "active_users",
            description="Usuários ativos",
            unit="1"
        )
        
    async def track_request(self, path: str, method: str, status_code: int, duration: float):
        """Registra métricas de requisição"""
        attributes = {
            "path": path,
            "method": method,
            "status": str(status_code)
        }
        
        self.request_counter.add(1, attributes)
        self.request_duration.record(duration, attributes)
        
        if status_code >= 400:
            self.error_counter.add(1, attributes)
            
    async def track_user_session(self, user_id: str, action: str):
        """Registra sessões de usuário"""
        if action == "login":
            self.active_users.add(1, {"user_id": user_id})
        elif action == "logout":
            self.active_users.add(-1, {"user_id": user_id})
            
    def create_span(self, name: str, attributes: Dict[str, Any] = None):
        """Cria um span de tracing"""
        return self.tracer.start_as_current_span(
            name,
            attributes=attributes or {}
        )
        
    def get_trace_context(self):
        """Obtém o contexto de tracing atual"""
        return TraceContextTextMapPropagator().extract({}) 