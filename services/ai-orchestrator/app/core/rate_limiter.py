from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from shared.cache import cache_manager
from app.core.config import settings

class RateLimiter:
    """
    Implementa limitação de taxa para requisições e tokens
    usando Redis como backend
    """
    
    def __init__(self):
        self.cache = cache_manager
    
    async def check_rate_limit(
        self,
        user_id: str,
        provider: str,
        token_count: Optional[int] = None
    ) -> bool:
        """
        Verifica se o usuário está dentro dos limites de taxa
        """
        # Chaves para o Redis
        req_key = f"rate_limit:requests:{provider}:{user_id}"
        token_key = f"rate_limit:tokens:{provider}:{user_id}"
        
        # Verificar limite de requisições
        req_count = await self.cache.get_rate_limit(req_key)
        if req_count >= settings.RATE_LIMIT_REQUESTS_PER_MIN:
            return False
        
        # Verificar limite de tokens se fornecido
        if token_count:
            token_sum = await self.cache.get_rate_limit(token_key)
            if token_sum + token_count > settings.RATE_LIMIT_TOKENS_PER_MIN:
                return False
        
        return True
    
    async def increment_counters(
        self,
        user_id: str,
        provider: str,
        token_count: Optional[int] = None
    ):
        """
        Incrementa os contadores de uso
        """
        # Chaves para o Redis
        req_key = f"rate_limit:requests:{provider}:{user_id}"
        token_key = f"rate_limit:tokens:{provider}:{user_id}"
        
        # Incrementar contador de requisições
        await self.cache.increment_rate_limit(
            req_key,
            amount=1,
            ttl=60  # 1 minuto
        )
        
        # Incrementar contador de tokens se fornecido
        if token_count:
            await self.cache.increment_rate_limit(
                token_key,
                amount=token_count,
                ttl=60  # 1 minuto
            )
    
    async def get_usage_stats(
        self,
        user_id: str,
        provider: str
    ) -> Dict[str, Any]:
        """
        Retorna estatísticas de uso atual
        """
        # Chaves para o Redis
        req_key = f"rate_limit:requests:{provider}:{user_id}"
        token_key = f"rate_limit:tokens:{provider}:{user_id}"
        
        # Obter contadores atuais
        req_count = await self.cache.get_rate_limit(req_key)
        token_count = await self.cache.get_rate_limit(token_key)
        
        return {
            "requests": {
                "current": req_count,
                "limit": settings.RATE_LIMIT_REQUESTS_PER_MIN,
                "remaining": max(0, settings.RATE_LIMIT_REQUESTS_PER_MIN - req_count)
            },
            "tokens": {
                "current": token_count,
                "limit": settings.RATE_LIMIT_TOKENS_PER_MIN,
                "remaining": max(0, settings.RATE_LIMIT_TOKENS_PER_MIN - token_count)
            }
        }

rate_limiter = RateLimiter() 