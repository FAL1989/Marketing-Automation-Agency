import time
import logging
from typing import Dict, Tuple, Optional
from app.core.redis import get_redis
from app.core.config import settings
from app.core.monitoring import MonitoringService
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)

class TokenBucketRateLimiter:
    """
    Implementa rate limiting usando Redis como backend com fallback local
    """
    def __init__(
        self,
        monitoring_service: MonitoringService,
        max_requests: int = settings.RATE_LIMIT_REQUESTS,
        window_size: int = settings.RATE_LIMIT_PERIOD,
        burst_size: Optional[int] = None,
        testing: bool = settings.TESTING
    ):
        self.monitoring_service = monitoring_service
        self.max_requests = max_requests
        self.window_size = window_size
        self.burst_size = burst_size or max_requests
        self.testing = testing
        
        # Prefixo para chaves Redis
        self.key_prefix = "rate_limit:"
        
        # Fallback local para quando Redis não está disponível
        self._local_storage = defaultdict(list)
    
    async def _get_key(self, identifier: str) -> str:
        """
        Gera chave Redis para o identificador
        """
        return f"{self.key_prefix}{identifier}"
    
    async def _check_local_rate_limit(self, identifier: str) -> Tuple[bool, Dict[str, str]]:
        """
        Verifica rate limit usando armazenamento local
        """
        now = int(time.time())
        window_start = now - self.window_size
        
        # Remove requisições antigas
        self._local_storage[identifier] = [
            ts for ts in self._local_storage[identifier]
            if ts > window_start
        ]
        
        current_requests = len(self._local_storage[identifier])
        
        headers = {
            "X-RateLimit-Limit": str(self.max_requests),
            "X-RateLimit-Remaining": str(max(0, self.max_requests - current_requests)),
            "X-RateLimit-Reset": str(now + self.window_size)
        }
        
        if current_requests >= self.max_requests:
            logger.warning(f"Rate limit local excedido para {identifier}")
            return False, headers
        
        self._local_storage[identifier].append(now)
        return True, headers
    
    async def check_rate_limit(self, identifier: str) -> Tuple[bool, Dict[str, str]]:
        """
        Verifica se o identificador excedeu o rate limit
        Retorna (allowed, headers)
        """
        # Em modo de teste, permite todas as requisições
        if self.testing:
            return True, {
                "X-RateLimit-Limit": str(self.max_requests),
                "X-RateLimit-Remaining": str(self.max_requests),
                "X-RateLimit-Reset": str(int(time.time()) + self.window_size)
            }
        
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                redis = await get_redis()
                key = await self._get_key(identifier)
                now = int(time.time())
                window_start = now - self.window_size
                
                # Pipeline para operações atômicas
                async with redis.pipeline(transaction=True) as pipe:
                    # Remove requisições antigas
                    await pipe.zremrangebyscore(key, 0, window_start)
                    # Conta requisições no período
                    await pipe.zcard(key)
                    # Executa o pipeline
                    results = await pipe.execute()
                    
                current_requests = results[1]
                
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
                retry_count += 1
                logger.warning(f"Tentativa {retry_count} de verificar rate limit falhou: {str(e)}")
                if retry_count < max_retries:
                    await asyncio.sleep(0.1 * retry_count)  # Backoff exponencial
                else:
                    logger.error(f"Fallback para rate limit local após {max_retries} tentativas")
                    return await self._check_local_rate_limit(identifier)
    
    async def get_limits(self, identifier: str) -> Dict[str, int]:
        """
        Retorna informações sobre os limites atuais
        """
        if self.testing:
            return {
                "limit": self.max_requests,
                "remaining": self.max_requests,
                "reset": int(time.time()) + self.window_size,
                "window": self.window_size
            }
            
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
            logger.warning(f"Usando limites locais: {str(e)}")
            current_requests = len(self._local_storage[identifier])
            return {
                "limit": self.max_requests,
                "remaining": max(0, self.max_requests - current_requests),
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
            logger.info(f"Limites Redis limpos para {identifier}")
        except Exception as e:
            logger.warning(f"Erro ao limpar limites Redis: {str(e)}")
        
        # Limpa também o armazenamento local
        if identifier in self._local_storage:
            del self._local_storage[identifier]
            logger.info(f"Limites locais limpos para {identifier}") 
    
    async def record_success(self, identifier: str):
        """
        Registra uma requisição bem sucedida
        """
        try:
            await self.monitoring_service.record_rate_limit_success(identifier)
        except Exception as e:
            logger.warning(f"Erro ao registrar sucesso para {identifier}: {str(e)}")

    async def record_failure(self, identifier: str, error: Exception):
        """
        Registra uma falha na requisição
        """
        try:
            await self.monitoring_service.record_rate_limit_failure(identifier, str(error))
        except Exception as e:
            logger.warning(f"Erro ao registrar falha para {identifier}: {str(e)}") 