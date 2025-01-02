from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from ..monitoring.security_metrics import SecurityMetrics
import time

class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware para coletar métricas de requisições"""
    
    async def dispatch(self, request: Request, call_next):
        """Processa a requisição e coleta métricas"""
        # Inicia o timer
        start_time = time.time()
        
        # Obtém o IP do cliente
        client_ip = request.client.host if request.client else "unknown"
        
        try:
            # Processa a requisição
            response = await call_next(request)
            
            # Registra a latência
            SecurityMetrics.record_request_latency(
                path=request.url.path,
                method=request.method,
                start_time=start_time
            )
            
            return response
            
        except Exception as e:
            # Em caso de erro, registra como acesso não autorizado
            SecurityMetrics.record_unauthorized_access(
                path=request.url.path,
                ip=client_ip,
                method=request.method
            )
            raise 