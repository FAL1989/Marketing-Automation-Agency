from typing import Dict, Any, List, Optional
import logging
from .base import AIProvider, AIRequest, AIResponse
from app.core.config import settings
from .providers.openai import OpenAIProvider
from .providers.anthropic import AnthropicProvider
from .providers.cohere import CohereProvider

logger = logging.getLogger(__name__)

class AIOrchestrator:
    def __init__(self):
        self.providers = {}
        self.cache = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """Inicializa os provedores de IA configurados"""
        if settings.OPENAI_API_KEY:
            from .providers.openai import OpenAIProvider
            self.providers["openai"] = OpenAIProvider()
        
        if settings.ANTHROPIC_API_KEY:
            from .providers.anthropic import AnthropicProvider
            self.providers["anthropic"] = AnthropicProvider()
        
        if settings.COHERE_API_KEY:
            from .providers.cohere import CohereProvider
            self.providers["cohere"] = CohereProvider()

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
            if cached := self.cache.get(cache_key):
                return {
                    "content": cached,
                    "source": "cache",
                    "cached": True
                }
        
        # Selecionar provedor
        provider = provider or settings.DEFAULT_PROVIDER
        if provider not in self.providers:
            raise ValueError(f"Provider {provider} não disponível")
        
        provider_instance = self.providers[provider]
        
        try:
            # Gerar conteúdo
            content = await provider_instance.generate(prompt, **kwargs)
            
            # Armazenar em cache se habilitado
            if settings.CACHE_ENABLED:
                self.cache[cache_key] = content
            
            return {
                "content": content,
                "source": provider,
                "cached": False,
                "tokens_used": provider_instance.last_token_count,
                "cost": provider_instance.last_cost
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar conteúdo com {provider}: {str(e)}")
            
            # Tentar fallback para outros provedores
            for fallback_provider in self.providers:
                if fallback_provider != provider:
                    try:
                        content = await self.providers[fallback_provider].generate(prompt, **kwargs)
                        return {
                            "content": content,
                            "source": f"{fallback_provider} (fallback)",
                            "cached": False,
                            "tokens_used": self.providers[fallback_provider].last_token_count,
                            "cost": self.providers[fallback_provider].last_cost
                        }
                    except:
                        continue
            
            # Se todos os provedores falharem, repassar o erro
            raise 