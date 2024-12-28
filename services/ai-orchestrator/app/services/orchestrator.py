from typing import Dict, Any, List, Optional
import json
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.providers import OpenAIProvider, AnthropicProvider, CohereProvider
from app.core.rate_limiter import rate_limiter
from app.core.config import settings
from shared.cache import cache_manager
from shared.messaging import message_broker

class AIOrchestrator:
    """
    Orquestra requisições entre diferentes provedores de IA,
    gerenciando rate limiting, cache e fallbacks
    """
    
    def __init__(self):
        self.providers = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "cohere": CohereProvider()
        }
        self.cache = cache_manager
    
    async def generate_content(
        self,
        prompt: str,
        user_id: str,
        provider: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Gera conteúdo usando o provedor especificado ou o melhor disponível
        """
        # Verificar cache se habilitado
        if settings.CACHE_ENABLED:
            cache_key = f"content:{hash(prompt)}"
            if cached := await self.cache.get(cache_key):
                return {
                    "content": cached,
                    "source": "cache",
                    "cached": True
                }
        
        # Selecionar provedor
        provider = provider or await self._select_best_provider(user_id)
        provider_instance = self.providers[provider]
        
        # Estimar tokens
        estimated_tokens = await provider_instance.count_tokens(prompt)
        
        # Verificar rate limit
        if not await rate_limiter.check_rate_limit(user_id, provider, estimated_tokens):
            # Tentar outro provedor se o atual estiver no limite
            for fallback_provider in self.providers.keys():
                if fallback_provider != provider:
                    if await rate_limiter.check_rate_limit(
                        user_id,
                        fallback_provider,
                        estimated_tokens
                    ):
                        provider = fallback_provider
                        provider_instance = self.providers[provider]
                        break
            else:
                raise Exception("Rate limit exceeded for all providers")
        
        try:
            # Gerar conteúdo
            content = await self._generate_with_retry(
                provider_instance,
                prompt,
                **kwargs
            )
            
            # Atualizar contadores
            await rate_limiter.increment_counters(
                user_id,
                provider,
                estimated_tokens
            )
            
            # Publicar evento de analytics
            await self._publish_analytics_event(
                user_id=user_id,
                provider=provider,
                prompt_tokens=estimated_tokens,
                completion_tokens=await provider_instance.count_tokens(content)
            )
            
            # Armazenar em cache se habilitado
            if settings.CACHE_ENABLED:
                await self.cache.set(
                    cache_key,
                    content,
                    ttl=settings.CACHE_TTL
                )
            
            return {
                "content": content,
                "source": provider,
                "cached": False
            }
            
        except Exception as e:
            # Em caso de erro, tentar outros provedores
            for fallback_provider in self.providers.keys():
                if fallback_provider != provider:
                    try:
                        content = await self._generate_with_retry(
                            self.providers[fallback_provider],
                            prompt,
                            **kwargs
                        )
                        return {
                            "content": content,
                            "source": f"{fallback_provider} (fallback)",
                            "cached": False
                        }
                    except:
                        continue
            
            # Se todos os provedores falharem, repassar o erro
            raise e
    
    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=settings.RETRY_DELAY)
    )
    async def _generate_with_retry(
        self,
        provider: Any,
        prompt: str,
        **kwargs
    ) -> str:
        """
        Tenta gerar conteúdo com retry em caso de falha
        """
        return await provider.generate(prompt, **kwargs)
    
    async def _select_best_provider(self, user_id: str) -> str:
        """
        Seleciona o melhor provedor baseado em disponibilidade e uso
        """
        best_provider = None
        max_remaining = -1
        
        for provider in self.providers.keys():
            stats = await rate_limiter.get_usage_stats(user_id, provider)
            remaining = stats["requests"]["remaining"]
            
            if remaining > max_remaining:
                max_remaining = remaining
                best_provider = provider
        
        return best_provider or "openai"  # OpenAI como fallback padrão
    
    async def _publish_analytics_event(
        self,
        user_id: str,
        provider: str,
        prompt_tokens: int,
        completion_tokens: int
    ):
        """
        Publica evento de analytics
        """
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "content_generation",
            "user_id": user_id,
            "provider": provider,
            "token_count": prompt_tokens + completion_tokens,
            "metadata": json.dumps({
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens
            })
        }
        
        await message_broker.publish(
            "content_analytics",
            event
        )

orchestrator = AIOrchestrator() 