from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from app.core.config import settings

def setup_cors(
    app: FastAPI,
    allowed_origins: Optional[List[str]] = None,
    allowed_methods: Optional[List[str]] = None,
    allowed_headers: Optional[List[str]] = None,
    allow_credentials: bool = True,
    max_age: int = 600
) -> None:
    """
    Configura o CORS para a aplicação com configurações seguras
    
    Args:
        app: Instância do FastAPI
        allowed_origins: Lista de origens permitidas
        allowed_methods: Lista de métodos HTTP permitidos
        allowed_headers: Lista de headers permitidos
        allow_credentials: Se permite credenciais
        max_age: Tempo máximo de cache das preflight requests
    """
    
    # Define valores padrão seguros
    default_origins = [
        "http://localhost:5173",  # Frontend dev
        "http://localhost:8000",  # Backend dev
        settings.FRONTEND_URL     # Produção
    ]
    
    default_methods = [
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "OPTIONS",
        "PATCH",
        "HEAD"
    ]
    
    default_headers = [
        "Accept",
        "Authorization",
        "Content-Type",
        "X-Requested-With",
        "X-CSRF-Token",
        "X-Real-IP",
        "X-Forwarded-For",
        "X-Forwarded-Proto",
        "X-Forwarded-Host",
        "X-Forwarded-Port",
        "Access-Control-Allow-Credentials",
        "Access-Control-Allow-Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers"
    ]
    
    # Validação adicional de origens
    if allowed_origins:
        for origin in allowed_origins:
            if not origin.startswith(("http://", "https://")):
                raise ValueError(f"Invalid origin format: {origin}")

    # Configuração do middleware CORS com opções de segurança
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins or default_origins,
        allow_credentials=allow_credentials,
        allow_methods=allowed_methods or default_methods,
        allow_headers=allowed_headers or default_headers,
        expose_headers=[
            "Content-Length",
            "Content-Range",
            "X-Total-Count",
            "X-Rate-Limit-Limit",
            "X-Rate-Limit-Remaining",
            "X-Rate-Limit-Reset"
        ],
        max_age=max_age
    ) 