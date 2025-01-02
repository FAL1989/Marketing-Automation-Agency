from enum import Enum
import time
import asyncio
from typing import Optional, Dict, Any, Callable, Awaitable
import logging
from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry
import structlog
from datetime import datetime, timedelta
from .notifications import notification_service
from .events import EventType
from functools import wraps

logger = structlog.get_logger()

# Registro dedicado para métricas do circuit breaker
CIRCUIT_BREAKER_REGISTRY = CollectorRegistry()

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

# Métricas do circuit breaker
CIRCUIT_STATE = get_or_create_metric(
    Gauge,
    'circuit_breaker_state',
    'Estado atual do circuit breaker (0=Closed, 1=Open, 2=Half-Open)',
    CIRCUIT_BREAKER_REGISTRY,
    labelnames=['service']
)

CIRCUIT_FAILURES = get_or_create_metric(
    Counter,
    'circuit_breaker_failures_total',
    'Total de falhas registradas pelo circuit breaker',
    CIRCUIT_BREAKER_REGISTRY,
    labelnames=['service', 'error_type']
)

CIRCUIT_SUCCESSES = get_or_create_metric(
    Counter,
    'circuit_breaker_successes_total',
    'Total de sucessos registrados pelo circuit breaker',
    CIRCUIT_BREAKER_REGISTRY,
    labelnames=['service']
)

CIRCUIT_TRANSITIONS = get_or_create_metric(
    Counter,
    'circuit_breaker_transitions_total',
    'Total de transições de estado do circuit breaker',
    CIRCUIT_BREAKER_REGISTRY,
    labelnames=['service', 'from_state', 'to_state']
)

REQUEST_DURATION = get_or_create_metric(
    Histogram,
    'circuit_breaker_request_duration_seconds',
    'Duração das requisições processadas pelo circuit breaker',
    CIRCUIT_BREAKER_REGISTRY,
    labelnames=['service', 'state'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half-open"

class CircuitBreaker:
    """
    Implementa o padrão Circuit Breaker com métricas detalhadas
    e notificações de mudança de estado
    """
    
    def __init__(
        self,
        service_name: str,
        failure_threshold: int = 20,
        reset_timeout: int = 15,
        half_open_timeout: int = 5,
        error_types: Optional[list[type]] = None
    ):
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_timeout = half_open_timeout
        self.error_types = error_types or [Exception]
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_start: Optional[float] = None
        self._lock = asyncio.Lock()
        
        # Inicializa métricas
        CIRCUIT_STATE.labels(service=service_name).set(0)
    
    @property
    def state(self) -> CircuitState:
        return self._state
    
    @property
    def failure_count(self) -> int:
        return self._failure_count
    
    async def _transition_state(self, new_state: CircuitState) -> None:
        """
        Realiza a transição de estado com notificações
        """
        if new_state != self._state:
            old_state = self._state
            self._state = new_state
            
            # Atualiza métricas
            CIRCUIT_STATE.labels(service=self.service_name).set(
                {
                    CircuitState.CLOSED: 0,
                    CircuitState.OPEN: 1,
                    CircuitState.HALF_OPEN: 2
                }[new_state]
            )
            
            CIRCUIT_TRANSITIONS.labels(
                service=self.service_name,
                from_state=old_state.value,
                to_state=new_state.value
            ).inc()
            
            # Notifica mudança de estado
            await notification_service.send_event(
                EventType.CIRCUIT_BREAKER_STATE_CHANGE,
                {
                    "service": self.service_name,
                    "old_state": old_state.value,
                    "new_state": new_state.value,
                    "failure_count": self._failure_count,
                    "last_failure": self._last_failure_time
                }
            )
            
            logger.info(
                "Circuit breaker state changed",
                service=self.service_name,
                old_state=old_state.value,
                new_state=new_state.value,
                failure_count=self._failure_count
            )
    
    async def _check_state_transition(self) -> None:
        """
        Verifica e realiza transições de estado baseado nas condições atuais
        """
        now = time.time()
        
        if self._state == CircuitState.OPEN:
            # Verifica se deve transicionar para half-open
            if now - self._last_failure_time >= self.reset_timeout:
                await self._transition_state(CircuitState.HALF_OPEN)
                self._half_open_start = now
        
        elif self._state == CircuitState.HALF_OPEN:
            # Verifica se excedeu o timeout do half-open
            if now - self._half_open_start >= self.half_open_timeout:
                # Se não houve falhas durante o período half-open, fecha o circuito
                if self._failure_count == 0:
                    await self._transition_state(CircuitState.CLOSED)
                else:
                    # Se houve falhas, volta para aberto
                    await self._transition_state(CircuitState.OPEN)
                    self._last_failure_time = now
    
    async def record_failure(self, error: Exception) -> None:
        """
        Registra uma falha e atualiza o estado do circuit breaker
        """
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            # Registra métricas
            error_type = type(error).__name__
            CIRCUIT_FAILURES.labels(
                service=self.service_name,
                error_type=error_type
            ).inc()
            
            # Verifica transição para estado aberto
            if self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    await self._transition_state(CircuitState.OPEN)
            
            elif self._state == CircuitState.HALF_OPEN:
                # Qualquer falha em half-open volta para aberto
                await self._transition_state(CircuitState.OPEN)
    
    async def record_success(self) -> None:
        """
        Registra um sucesso e atualiza o estado do circuit breaker
        """
        async with self._lock:
            # Registra métricas
            CIRCUIT_SUCCESSES.labels(service=self.service_name).inc()
            
            if self._state == CircuitState.HALF_OPEN:
                # Sucesso em half-open fecha o circuito
                self._failure_count = 0
                await self._transition_state(CircuitState.CLOSED)
            
            elif self._state == CircuitState.CLOSED:
                # Reseta contador de falhas em caso de sucesso
                self._failure_count = 0
    
    async def call(
        self,
        func: Callable[..., Awaitable[Any]],
        *args,
        **kwargs
    ) -> Any:
        """
        Executa uma função protegida pelo circuit breaker
        """
        async with self._lock:
            await self._check_state_transition()
            
            if self._state == CircuitState.OPEN:
                raise Exception(f"Circuit breaker for {self.service_name} is OPEN")
        
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            
            # Registra sucesso e duração
            duration = time.time() - start_time
            REQUEST_DURATION.labels(
                service=self.service_name,
                state=self._state.value
            ).observe(duration)
            
            await self.record_success()
            return result
            
        except Exception as e:
            # Verifica se é um tipo de erro monitorado
            if any(isinstance(e, error_type) for error_type in self.error_types):
                # Registra falha e duração
                duration = time.time() - start_time
                REQUEST_DURATION.labels(
                    service=self.service_name,
                    state=self._state.value
                ).observe(duration)
                
                await self.record_failure(e)
            
            raise e
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Retorna o status atual do circuit breaker
        """
        return {
            "service": self.service_name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure": self._last_failure_time,
            "half_open_start": self._half_open_start,
            "reset_timeout": self.reset_timeout,
            "half_open_timeout": self.half_open_timeout
        } 