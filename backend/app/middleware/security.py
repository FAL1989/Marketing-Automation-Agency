from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from ..core.config import settings
from ..core import monitoring
import re
import time

class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware para segurança da aplicação"""
    
    def __init__(self, app):
        super().__init__(app)
        self.suspicious_patterns = [
            r"UNION\s+SELECT",  # SQL Injection
            r"exec\s+xp_",      # SQL Injection
            r"\.\.\/",          # Path Traversal
            r"<script>",        # XSS
            r"\.\.\\",          # Path Traversal
            r"%2e%2e%2f"       # Encoded Path Traversal
        ]
        
        # Define a política CSP
        self.csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' https:; "
            "media-src 'self'; "
            "object-src 'none'; "
            "frame-src 'self'; "
            "worker-src 'self' blob:; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "base-uri 'self'; "
            "manifest-src 'self'"
        )
        
        # Define a política de permissões
        self.permissions_policy = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )
        
    async def __call__(self, scope, receive, send):
        """Processa a requisição aplicando medidas de segurança"""
        request = Request(scope, receive=receive)
        start_time = time.time()
        
        # Verifica padrões suspeitos
        if self._has_suspicious_patterns(request):
            monitoring.track_suspicious_pattern("malicious_pattern", "anonymous")
            response = Response(
                content="Forbidden",
                status_code=403
            )
            await response(scope, receive, send)
            return
            
        # Adiciona headers de segurança
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                headers.extend([
                    # Headers existentes
                    (b"X-Content-Type-Options", b"nosniff"),
                    (b"X-Frame-Options", b"DENY"),
                    (b"X-XSS-Protection", b"1; mode=block"),
                    
                    # Novos headers de segurança
                    (b"Content-Security-Policy", self.csp_policy.encode()),
                    (b"Strict-Transport-Security", b"max-age=31536000; includeSubDomains; preload"),
                    (b"Referrer-Policy", b"strict-origin-when-cross-origin"),
                    (b"Permissions-Policy", self.permissions_policy.encode()),
                    (b"Cross-Origin-Resource-Policy", b"same-origin"),
                    (b"Cross-Origin-Opener-Policy", b"same-origin"),
                    (b"Cross-Origin-Embedder-Policy", b"require-corp")
                ])
            await send(message)
            
        # Processa a requisição
        await self.app(scope, receive, send_wrapper)
        
        # Registra a latência
        duration = time.time() - start_time
        monitoring.track_request_latency(request.url.path, duration)
        
    def _has_suspicious_patterns(self, request: Request) -> bool:
        """Verifica se a requisição contém padrões suspeitos"""
        # Verifica a query string
        query = request.query_params.__str__()
        for pattern in self.suspicious_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
                
        # Verifica o path
        path = request.url.path
        for pattern in self.suspicious_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                return True
                
        # Verifica os headers
        headers = request.headers.__str__()
        for pattern in self.suspicious_patterns:
            if re.search(pattern, headers, re.IGNORECASE):
                return True
                
        return False 