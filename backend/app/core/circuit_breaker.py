from enum import Enum
import time
from collections import deque
from typing import Callable, Any, Optional, Deque, Tuple
import asyncio
import structlog
from datetime import datetime, timedelta

logger = structlog.get_logger()

class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_trials: int = 3,
        window_size: int = 100,
        window_duration: float = 60.0
    ):
        self.config = {
            'failure_threshold': failure_threshold,
            'recovery_timeout': recovery_timeout,
            'half_open_max_trials': half_open_max_trials,
            'window_size': window_size,
            'window_duration': window_duration
        }
        self.state = CircuitState.CLOSED
        self.metrics = {
            'failures': 0,
            'last_failure_time': 0,
            'half_open_trials': 0,
            'last_state_change': time.time(),
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_latency': 0
        }
        self.windows = {
            'request': deque(maxlen=window_size),
            'latency': deque(maxlen=window_size),
            'error': deque(maxlen=window_size)
        }
        self.state_changes = []

    def _clean_windows(self):
        current_time = time.time()
        cutoff = current_time - self.config['window_duration']
        for window in self.windows.values():
            while window and window[0]["timestamp"] < cutoff:
                window.popleft()

    def _calculate_metrics(self) -> Tuple[float, float]:
        self._clean_windows()
        error_rate = (len([e for e in self.windows['error'] if e["is_error"]]) / 
                     len(self.windows['error']) * 100 if self.windows['error'] else 0)
        avg_latency = (sum(l["latency"] for l in self.windows['latency']) / 
                      len(self.windows['latency']) if self.windows['latency'] else 0)
        return error_rate, avg_latency

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == CircuitState.OPEN:
            if time.time() - self.metrics['last_failure_time'] >= self.config['recovery_timeout']:
                self._transition_to(CircuitState.HALF_OPEN)
            else:
                raise Exception(f"Circuit breaker is OPEN. Retry after {self.config['recovery_timeout'] - (time.time() - self.metrics['last_failure_time']):.1f}s")

        start_time = time.time()
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self._record_success(time.time() - start_time)
            return result
        except Exception as e:
            self._record_failure(time.time() - start_time)
            raise

    def _record_success(self, latency: float):
        self.metrics['successful_requests'] += 1
        self._update_metrics(latency, False)
        if self.state == CircuitState.HALF_OPEN:
            self.metrics['half_open_trials'] += 1
            if self.metrics['half_open_trials'] >= self.config['half_open_max_trials']:
                self._transition_to(CircuitState.CLOSED)

    def _record_failure(self, latency: float):
        self.metrics['failures'] += 1
        self.metrics['failed_requests'] += 1
        self.metrics['last_failure_time'] = time.time()
        self._update_metrics(latency, True)
        
        error_rate, avg_latency = self._calculate_metrics()
        if error_rate >= 50.0 or avg_latency >= 5.0 or self.metrics['failures'] >= self.config['failure_threshold']:
            if self.state in [CircuitState.CLOSED, CircuitState.HALF_OPEN]:
                self._transition_to(CircuitState.OPEN)

    def _update_metrics(self, latency: float, is_error: bool):
        current_time = time.time()
        entry = {"timestamp": current_time, "is_error": is_error}
        self.windows['request'].append(entry)
        self.windows['latency'].append({"timestamp": current_time, "latency": latency})
        self.windows['error'].append(entry)
        self.metrics['total_requests'] += 1
        self.metrics['total_latency'] += latency

    def _transition_to(self, new_state: CircuitState):
        old_state = self.state
        self.state = new_state
        self.metrics['last_state_change'] = time.time()
        
        if new_state == CircuitState.CLOSED:
            self.metrics['failures'] = self.metrics['half_open_trials'] = 0
        elif new_state == CircuitState.HALF_OPEN:
            self.metrics['half_open_trials'] = 0
            
        self.state_changes.append({
            'from': old_state.value,
            'to': new_state.value,
            'timestamp': self.metrics['last_state_change'],
            'metrics': self.get_metrics()
        })
        
        logger.info(
            "circuit_breaker_state_change",
            old_state=old_state.value,
            new_state=new_state.value,
            metrics=self._calculate_metrics()
        )

    def get_metrics(self) -> dict:
        """Retorna métricas detalhadas do circuit breaker"""
        current_time = time.time()
        
        return {
            "state": self.state.value,
            "total_requests": self.metrics['total_requests'],
            "successful_requests": self.metrics['successful_requests'],
            "failed_requests": self.metrics['failed_requests'],
            "current_failures": self.metrics['failures'],
            "success_rate": (self.metrics['successful_requests'] / self.metrics['total_requests'] * 100) 
                if self.metrics['total_requests'] > 0 else 0,
            "error_rate": self._calculate_metrics()[0],
            "avg_latency": self._calculate_metrics()[1],
            "last_state_change": self.metrics['last_state_change'],
            "time_since_last_change": current_time - self.metrics['last_state_change'],
            "window_metrics": {
                "size": len(self.windows['request']),
                "duration": self.config['window_duration'],
                "requests_in_window": len(self.windows['request']),
                "errors_in_window": len([e for e in self.windows['error'] if e["is_error"]])
            },
            "state_changes": self.state_changes[-10:]  # Últimas 10 mudanças de estado
        }
        
    def reset(self):
        """Reseta o circuit breaker para o estado inicial"""
        self._transition_to(CircuitState.CLOSED)
        self.metrics['failures'] = 0
        self.metrics['half_open_trials'] = 0
        self.metrics['last_failure_time'] = 0
        for window in self.windows.values():
            window.clear()
        self.metrics['total_requests'] = 0
        self.metrics['successful_requests'] = 0
        self.metrics['failed_requests'] = 0
        self.metrics['total_latency'] = 0
        self.state_changes = [] 