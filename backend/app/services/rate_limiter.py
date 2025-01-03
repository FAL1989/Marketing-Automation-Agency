import time
import logging
from typing import Dict, Tuple, Optional
from app.core.redis import get_redis
from app.core.config import settings
from app.core.monitoring import MonitoringService

logger = logging.getLogger(__name__)

class TokenBucketRateLimiter:
    """
    Implementa rate limiting usando Redis como backend
    """
    def __init__(
        self,
        monitoring_service: MonitoringService,
        max_requests: int = settings.RATE_LIMIT_REQUESTS,
        window_size: int = settings.RATE_LIMIT_PERIOD,
        burst_size: Optional[int] = None
    ):
        self.monitoring_service = monitoring_service
        self.max_requests = max_requests
        self.window_size = window_size
        self.burst_size = burst_size or max_requests
        
        # Prefixo para chaves Redis
        self.key_prefix = "rate_limit:"
    
    async def _get_key(self, identifier: str) -> str:
        """
        Gera chave Redis para o identificador
        """
        return f"{self.key_prefix}{identifier}"
    
    async def check_rate_limit(self, identifier: str) -> Tuple[bool, Dict[str, str]]:
        """
        Verifica se o identificador excedeu o rate limit
        Retorna (allowed, headers)
        """
        try:
            redis = await get_redis()
            key = await self._get_key(identifier)
            now = int(time.time())
            window_start = now - self.window_size
            
            # Remove requisições antigas
            await redis.zremrangebyscore(key, 0, window_start)
            
            # Conta requisições no período
            current_requests = await redis.zcard(key)
            
            # Prepara headers
            headers = {
                "X-RateLimit-Limit": str(self.max_requests),
                "X-RateLimit-Remaining": str(max(0, self.max_requests - current_requests)),
                "X-RateLimit-Reset": str(now + self.window_size)
            }
            
            # Verifica limite
            if current_requests >= self.max_requests:
                logger.warning(f"Rate limit excedido para {identifier}")
                await self.monitoring_service.record_rate_limit(
                    endpoint=identifier,
                    current=current_requests,
                    exceeded=True
                )
                return False, headers
            
            # Adiciona nova requisição
            await redis.zadd(key, {str(now): now})
            
            # Define TTL para limpeza automática
            await redis.expire(key, self.window_size * 2)
            
            # Registra métricas
            await self.monitoring_service.record_rate_limit(
                endpoint=identifier,
                current=current_requests + 1
            )
            
            return True, headers
            
        except Exception as e:
            logger.error(f"Erro ao verificar rate limit: {str(e)}")
            # Em caso de erro, permite a requisição
            return True, {}
    
    async def get_limits(self, identifier: str) -> Dict[str, int]:
        """
        Retorna informações sobre os limites atuais
        """
        try:
            redis = await get_redis()
            key = await self._get_key(identifier)
            now = int(time.time())
            window_start = now - self.window_size
            
            # Remove requisições antigas
            await redis.zremrangebyscore(key, 0, window_start)
            
            # Conta requisições no período
            current_requests = await redis.zcard(key)
            
            return {
                "limit": self.max_requests,
                "remaining": max(0, self.max_requests - current_requests),
                "reset": now + self.window_size,
                "window": self.window_size
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter limites: {str(e)}")
            return {
                "limit": self.max_requests,
                "remaining": self.max_requests,
                "reset": int(time.time()) + self.window_size,
                "window": self.window_size
            }
    
    async def clear_limits(self, identifier: str):
        """
        Limpa os limites para um identificador
        """
        try:
            redis = await get_redis()
            key = await self._get_key(identifier)
            await redis.delete(key)
            logger.info(f"Limites limpos para {identifier}")
            
        except Exception as e:
            logger.error(f"Erro ao limpar limites: {str(e)}")
            raise 