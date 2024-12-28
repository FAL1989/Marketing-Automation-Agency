from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response, JSONResponse
from typing import Dict
from ..core.circuit_breaker import CircuitBreaker
import structlog
from datetime import datetime

logger = structlog.get_logger()

DEFAULT_CONFIG = {
    "failure_threshold": 5,
    "recovery_timeout": 30.0,
    "half_open_max_trials": 3,
    "window_size": 100,
    "window_duration": 60.0
}

class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, endpoints_config: Dict[str, dict] = None):
        """
        Inicializa o middleware com configurações específicas para endpoints
        
        Args:
            app: Aplicação FastAPI
            endpoints_config: Dicionário com configurações por endpoint
                Ex: {
                    "/api/slow-endpoint": {
                        "failure_threshold": 3,
                        "recovery_timeout": 30.0,
                        "window_size": 100,
                        "window_duration": 60.0
                    }
                }
        """
        super().__init__(app)
        self.circuit_breakers = {}
        self.endpoints_config = endpoints_config or {}
        
        # Cria circuit breakers para cada endpoint configurado
        for endpoint, config in self.endpoints_config.items():
            # Mescla configurações default com as específicas do endpoint
            endpoint_config = DEFAULT_CONFIG.copy()
            endpoint_config.update(config)
            self.circuit_breakers[endpoint] = CircuitBreaker(**endpoint_config)
            
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        
        # Se o endpoint não está configurado para circuit breaking, passa direto
        if path not in self.circuit_breakers:
            return await call_next(request)
            
        circuit_breaker = self.circuit_breakers[path]
        
        try:
            # Executa a requisição através do circuit breaker
            response = await circuit_breaker.call(call_next, request)
            return response
            
        except Exception as e:
            logger.error(
                "circuit_breaker_error",
                path=path,
                error=str(e),
                state=circuit_breaker.state.value,
                metrics=circuit_breaker.get_metrics()
            )
            
            # Se o circuito está aberto, retorna 503
            if "Circuit breaker is OPEN" in str(e):
                metrics = circuit_breaker.get_metrics()
                retry_after = int(circuit_breaker.recovery_timeout - (datetime.now().timestamp() - circuit_breaker.last_failure_time))
                
                return JSONResponse(
                    status_code=503,
                    headers={
                        "Retry-After": str(max(1, retry_after))
                    },
                    content={
                        "detail": "Service temporarily unavailable",
                        "retry_after": max(1, retry_after),
                        "circuit_breaker_metrics": metrics
                    }
                )
            
            # Para outros erros, propaga a exceção
            raise
            
    def get_metrics(self) -> Dict[str, dict]:
        """Retorna métricas de todos os circuit breakers"""
        return {
            endpoint: cb.get_metrics()
            for endpoint, cb in self.circuit_breakers.items()
        }
        
    def reset_all(self):
        """Reseta todos os circuit breakers"""
        for cb in self.circuit_breakers.values():
            cb.reset() 