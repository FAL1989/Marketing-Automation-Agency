from typing import List
from fastapi import Request, HTTPException, status, FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import re
import structlog
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from .config import settings

logger = structlog.get_logger()

# Padrões suspeitos para detecção
SUSPICIOUS_PATTERNS = [
    r'UNION\s+SELECT',
    r'exec\s+xp_',
    r'\.\./etc/passwd',
    r'<script>.*?</script>',
    r'\.\./\.\.',
    r'%2e%2e%2f'
]

class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Verificar padrões suspeitos na URL e headers
        url = str(request.url)
        headers = dict(request.headers)
        
        for pattern in SUSPICIOUS_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                logger.warning("suspicious_pattern_detected", 
                             pattern=pattern, 
                             url=url,
                             client_ip=request.client.host)
                raise HTTPException(status_code=403, detail="Suspicious pattern detected")
            
            for header_value in headers.values():
                if re.search(pattern, str(header_value), re.IGNORECASE):
                    logger.warning("suspicious_header_detected",
                                 pattern=pattern,
                                 header_value=header_value,
                                 client_ip=request.client.host)
                    raise HTTPException(status_code=403, detail="Suspicious pattern detected in headers")

        response = await call_next(request)
        
        # Adicionar headers de segurança
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

def setup_cors(app: FastAPI):
    """Configura o middleware CORS"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def setup_security_middleware(app: FastAPI):
    """Configura middlewares de segurança"""
    # Trusted Host Middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts_list,
    )
    app.add_middleware(SecurityMiddleware) 