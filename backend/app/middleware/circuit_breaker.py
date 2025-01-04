from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response, JSONResponse
from typing import Dict
from ..core.circuit_breaker import CircuitBreaker, CircuitState
import structlog
from datetime import datetime

logger = structlog.get_logger()

DEFAULT_CONFIG = {
    "service_name": "default",
    "failure_threshold": 5,
    "reset_timeout": 30,
    "half_open_timeout": 5
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
                        "service_name": "slow_endpoint",
                        "failure_threshold": 3,
                        "reset_timeout": 30,
                        "half_open_timeout": 5
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
            if "service_name" not in endpoint_config:
                endpoint_config["service_name"] = endpoint.replace("/", "_")
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
                state=circuit_breaker.state.value
            )
            
            # Se o circuito está aberto, retorna 503
            if "Circuit breaker is OPEN" in str(e):
                status = await circuit_breaker.get_status()
                retry_after = int(status["reset_timeout"] - (datetime.now().timestamp() - status["last_failure"]))
                
                return JSONResponse(
                    status_code=503,
                    headers={
                        "Retry-After": str(max(1, retry_after))
                    },
                    content={
                        "detail": "Service temporarily unavailable",
                        "retry_after": max(1, retry_after),
                        "circuit_breaker_status": status
                    }
                )
            
            # Para outros erros, propaga a exceção
            raise
            
    async def get_metrics(self) -> Dict[str, dict]:
        """Retorna métricas de todos os circuit breakers"""
        metrics = {}
        for endpoint, cb in self.circuit_breakers.items():
            try:
                status = await cb.get_status()
                metrics[endpoint] = status
            except Exception as e:
                logger.error(f"Erro ao obter métricas para {endpoint}: {e}")
                metrics[endpoint] = {
                    "error": str(e),
                    "state": "unknown"
                }
        return metrics
        
    async def reset_all(self):
        """Reseta todos os circuit breakers"""
        for cb in self.circuit_breakers.values():
            await cb._transition_state(CircuitState.CLOSED)
            cb._failure_count = 0
            cb._last_failure_time = None
            cb._half_open_start = None 