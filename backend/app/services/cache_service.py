from typing import Optional, Any, Dict
import hashlib
import json
import redis
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_client = redis.from_url(redis_url)
        self.default_ttl = timedelta(hours=24)
    
    def _generate_key(self, prompt: str, variables: Dict[str, Any], provider: str) -> str:
        """
        Gera uma chave única para o cache baseada no prompt, variáveis e provedor.
        Usa hash SHA-256 para garantir chaves consistentes e de tamanho fixo.
        """
        cache_data = {
            "prompt": prompt,
            "variables": variables,
            "provider": provider
        }
        data_str = json.dumps(cache_data, sort_keys=True)
        return f"ai_generation:{hashlib.sha256(data_str.encode()).hexdigest()}"
    
    async def get_cached_response(
        self,
        prompt: str,
        variables: Dict[str, Any],
        provider: str
    ) -> Optional[str]:
        """
        Recupera uma resposta cacheada se disponível.
        
        Args:
            prompt: O prompt original
            variables: Variáveis usadas no prompt
            provider: O provedor de IA usado
            
        Returns:
            Optional[str]: A resposta cacheada ou None se não encontrada
        """
        try:
            key = self._generate_key(prompt, variables, provider)
            cached = self.redis_client.get(key)
            if cached:
                logger.info(f"Cache hit para key: {key}")
                return cached.decode('utf-8')
            logger.info(f"Cache miss para key: {key}")
            return None
        except Exception as e:
            logger.error(f"Erro ao recuperar do cache: {str(e)}")
            return None
    
    async def cache_response(
        self,
        prompt: str,
        variables: Dict[str, Any],
        provider: str,
        response: str,
        ttl: Optional[timedelta] = None
    ) -> bool:
        """
        Armazena uma resposta no cache.
        
        Args:
            prompt: O prompt original
            variables: Variáveis usadas no prompt
            provider: O provedor de IA usado
            response: A resposta a ser cacheada
            ttl: Tempo de vida do cache (opcional)
            
        Returns:
            bool: True se o cache foi bem sucedido, False caso contrário
        """
        try:
            key = self._generate_key(prompt, variables, provider)
            ttl = ttl or self.default_ttl
            self.redis_client.setex(
                key,
                ttl,
                response
            )
            logger.info(f"Resposta cacheada com sucesso para key: {key}")
            return True
        except Exception as e:
            logger.error(f"Erro ao cachear resposta: {str(e)}")
            return False
    
    async def invalidate_cache(
        self,
        prompt: str,
        variables: Dict[str, Any],
        provider: str
    ) -> bool:
        """
        Invalida uma entrada específica do cache.
        
        Args:
            prompt: O prompt original
            variables: Variáveis usadas no prompt
            provider: O provedor de IA usado
            
        Returns:
            bool: True se a invalidação foi bem sucedida, False caso contrário
        """
        try:
            key = self._generate_key(prompt, variables, provider)
            self.redis_client.delete(key)
            logger.info(f"Cache invalidado com sucesso para key: {key}")
            return True
        except Exception as e:
            logger.error(f"Erro ao invalidar cache: {str(e)}")
            return False
    
    def clear_all_cache(self) -> bool:
        """
        Limpa todo o cache relacionado a gerações de IA.
        
        Returns:
            bool: True se a limpeza foi bem sucedida, False caso contrário
        """
        try:
            pattern = "ai_generation:*"
            cursor = 0
            while True:
                cursor, keys = self.redis_client.scan(cursor, pattern)
                if keys:
                    self.redis_client.delete(*keys)
                if cursor == 0:
                    break
            logger.info("Cache limpo com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {str(e)}")
            return False
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Retorna estatísticas sobre o uso do cache.
        
        Returns:
            Dict[str, int]: Dicionário com estatísticas do cache
        """
        try:
            pattern = "ai_generation:*"
            cursor = 0
            total_keys = 0
            while True:
                cursor, keys = self.redis_client.scan(cursor, pattern)
                total_keys += len(keys)
                if cursor == 0:
                    break
            
            info = self.redis_client.info()
            return {
                "total_entries": total_keys,
                "used_memory": info["used_memory"],
                "hits": info["keyspace_hits"],
                "misses": info["keyspace_misses"]
            }
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do cache: {str(e)}")
            return {
                "total_entries": 0,
                "used_memory": 0,
                "hits": 0,
                "misses": 0
            } 