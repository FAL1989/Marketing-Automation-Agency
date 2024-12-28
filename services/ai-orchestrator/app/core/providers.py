from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import openai
import anthropic
import cohere
from app.core.config import settings

class AIProvider(ABC):
    """Classe base abstrata para provedores de IA"""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Gera conteúdo baseado no prompt"""
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """Conta tokens no texto"""
        pass

class OpenAIProvider(AIProvider):
    """Implementação do provedor OpenAI"""
    
    def __init__(self):
        self.client = openai.AsyncClient(api_key=settings.OPENAI_API_KEY)
        self.config = settings.MODEL_CONFIGS["openai"]
    
    async def generate(self, prompt: str, **kwargs) -> str:
        try:
            model = kwargs.get("model", self.config["default_model"])
            response = await self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", self.config["temperature"]),
                max_tokens=kwargs.get("max_tokens", self.config["max_tokens"])
            )
            return response.choices[0].message.content
        except Exception as e:
            if "model" in kwargs:  # Já está usando modelo de fallback
                raise e
            # Tentar com modelo de fallback
            return await self.generate(
                prompt,
                model=self.config["fallback_model"],
                **kwargs
            )
    
    async def count_tokens(self, text: str) -> int:
        # Estimativa aproximada (1 token ≈ 4 caracteres)
        return len(text) // 4

class AnthropicProvider(AIProvider):
    """Implementação do provedor Anthropic"""
    
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.config = settings.MODEL_CONFIGS["anthropic"]
    
    async def generate(self, prompt: str, **kwargs) -> str:
        try:
            model = kwargs.get("model", self.config["default_model"])
            response = await self.client.messages.create(
                model=model,
                max_tokens=kwargs.get("max_tokens", self.config["max_tokens"]),
                temperature=kwargs.get("temperature", self.config["temperature"]),
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            if "model" in kwargs:  # Já está usando modelo de fallback
                raise e
            # Tentar com modelo de fallback
            return await self.generate(
                prompt,
                model=self.config["fallback_model"],
                **kwargs
            )
    
    async def count_tokens(self, text: str) -> int:
        # Estimativa aproximada (1 token ≈ 4 caracteres)
        return len(text) // 4

class CohereProvider(AIProvider):
    """Implementação do provedor Cohere"""
    
    def __init__(self):
        self.client = cohere.AsyncClient(api_key=settings.COHERE_API_KEY)
        self.config = settings.MODEL_CONFIGS["cohere"]
    
    async def generate(self, prompt: str, **kwargs) -> str:
        try:
            model = kwargs.get("model", self.config["default_model"])
            response = await self.client.generate(
                prompt=prompt,
                model=model,
                max_tokens=kwargs.get("max_tokens", self.config["max_tokens"]),
                temperature=kwargs.get("temperature", self.config["temperature"])
            )
            return response.generations[0].text
        except Exception as e:
            if "model" in kwargs:  # Já está usando modelo de fallback
                raise e
            # Tentar com modelo de fallback
            return await self.generate(
                prompt,
                model=self.config["fallback_model"],
                **kwargs
            )
    
    async def count_tokens(self, text: str) -> int:
        # Estimativa aproximada (1 token ≈ 4 caracteres)
        return len(text) // 4

class ProviderFactory:
    _providers: Dict[str, AIProvider] = {
        "openai": OpenAIProvider(),
        "anthropic": AnthropicProvider(),
        "cohere": CohereProvider()
    }
    
    @classmethod
    def get_provider(cls, provider_name: str) -> AIProvider:
        provider = cls._providers.get(provider_name)
        if not provider:
            raise ValueError(f"Provider {provider_name} não encontrado")
        return provider 