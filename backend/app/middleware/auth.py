from fastapi import Request, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from starlette.middleware.base import BaseHTTPMiddleware
from ..core.config import settings
from ..services.rate_limiter import TokenBucketRateLimiter
from ..dependencies import get_current_user, get_redis_client
import structlog
from typing import Optional
import json
from datetime import datetime
import asyncio
import random

logger = structlog.get_logger()

class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware para autenticação e rate limiting"""
    
    def __init__(self, app, rate_limiter: TokenBucketRateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
        
        # Rotas públicas que não precisam de autenticação
        self.public_routes = {
            "/auth/login",
            "/auth/register",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/metrics",
            "/health"
        }
        
        # Cache de tokens inválidos (blacklist)
        self._invalid_tokens = set()
        self._invalid_tokens_lock = asyncio.Lock()
    
    async def _check_token(self, token: str, redis) -> bool:
        """Verifica se o token está na blacklist"""
        # Verifica cache local primeiro
        if token in self._invalid_tokens:
            return False
            
        # Verifica Redis se disponível
        if redis:
            try:
                return await redis.exists(f"blacklist:{token}")
            except Exception as e:
                logger.error("Erro ao verificar blacklist no Redis", error=str(e))
        
        return True
    
    async def _handle_auth(self, request: Request, token: str, redis):
        """Obtém usuário atual"""
        if not await self._check_token(token, redis):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalid")
            
        user = await get_current_user(token)
        request.state.user = user
        return "enterprise" if user.is_superuser else ("premium" if user.is_premium else "free")
    
    async def dispatch(self, request: Request, call_next):
        """Processa a requisição"""
        path = request.url.path
        
        # Ignora rotas públicas
        if path in self.public_routes:
            return await call_next(request)
        
        # Extrai e valida o token
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        
        # Obtém cliente Redis
        redis = await get_redis_client()
        
        try:
            # Verifica blacklist
            if not await self._check_token(token, redis):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token is invalid or expired",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Obtém usuário atual
            user_type = await self._handle_auth(request, token, redis)
            
            # Aplica rate limiting
            allowed, info = await self.rate_limiter.is_allowed(token, path, user_type)
            
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    headers={"Retry-After": str(info["reset"] - int(datetime.utcnow().timestamp()))}
                )
            
            request.state.rate_limit_info = info
            response = await call_next(request)
            
            # Adiciona headers de rate limit na resposta
            for key, value in info.items():
                response.headers[f"X-RateLimit-{key.title()}"] = str(value)
            
            return response
            
        except HTTPException as e:
            # Se o token for inválido, adiciona à blacklist
            if e.status_code == status.HTTP_401_UNAUTHORIZED:
                async with self._invalid_tokens_lock:
                    self._invalid_tokens.add(token)
                    if redis:
                        await redis.setex(f"blacklist:{token}", settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, "1")
            raise
            
        except Exception as e:
            logger.error("Erro no middleware de autenticação", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
        
        finally:
            # Limpa tokens inválidos periodicamente
            if random.random() < 0.01:  # 1% de chance
                await self._clean_invalid_tokens() 