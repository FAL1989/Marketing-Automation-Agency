from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from enum import Enum
import openai
import anthropic
import cohere
from app.core.config import settings

class ProviderType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic" 
    COHERE = "cohere"

class ProviderConfig(BaseModel):
    provider: ProviderType
    model: str
    api_key: str
    
class ProviderManager:
    """Manages LLM providers with fallback support"""
    
    def __init__(self):
        self.providers: List[ProviderConfig] = []
        self._initialize_providers()
        
    def _initialize_providers(self):
        """Initialize available providers from settings"""
        if settings.OPENAI_API_KEY:
            self.providers.append(
                ProviderConfig(
                    provider=ProviderType.OPENAI,
                    model="gpt-4",
                    api_key=settings.OPENAI_API_KEY
                )
            )
            
        if settings.ANTHROPIC_API_KEY:
            self.providers.append(
                ProviderConfig(
                    provider=ProviderType.ANTHROPIC,
                    model="claude-2",
                    api_key=settings.ANTHROPIC_API_KEY
                )
            )
            
        if settings.COHERE_API_KEY:
            self.providers.append(
                ProviderConfig(
                    provider=ProviderType.COHERE,
                    model="command",
                    api_key=settings.COHERE_API_KEY
                )
            )
            
    async def get_completion(self, prompt: str, provider_type: Optional[ProviderType] = None) -> str:
        """Get completion with fallback support"""
        errors = []
        
        # Try specified provider first
        if provider_type:
            provider = next((p for p in self.providers if p.provider == provider_type), None)
            if provider:
                try:
                    return await self._get_completion_from_provider(prompt, provider)
                except Exception as e:
                    errors.append(f"Error with {provider_type}: {str(e)}")
        
        # Try all providers in order
        for provider in self.providers:
            try:
                return await self._get_completion_from_provider(prompt, provider)
            except Exception as e:
                errors.append(f"Error with {provider.provider}: {str(e)}")
                continue
                
        raise Exception(f"All providers failed: {'; '.join(errors)}")
        
    async def _get_completion_from_provider(self, prompt: str, provider: ProviderConfig) -> str:
        """Get completion from specific provider"""
        if provider.provider == ProviderType.OPENAI:
            openai.api_key = provider.api_key
            response = await openai.ChatCompletion.acreate(
                model=provider.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
            
        elif provider.provider == ProviderType.ANTHROPIC:
            client = anthropic.Client(api_key=provider.api_key)
            response = client.completion(
                prompt=f"\n\nHuman: {prompt}\n\nAssistant:",
                model=provider.model,
                max_tokens_to_sample=1000
            )
            return response.completion
            
        elif provider.provider == ProviderType.COHERE:
            co = cohere.Client(provider.api_key)
            response = co.generate(
                prompt=prompt,
                model=provider.model,
                max_tokens=1000
            )
            return response.generations[0].text
            
        raise ValueError(f"Unknown provider: {provider.provider}")

# Global provider manager instance
provider_manager = ProviderManager() 