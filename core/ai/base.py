from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
import openai
import os
from ..monitoring.metrics import monitor_ai_request, logger

class AIRequest(BaseModel):
    """Modelo base para requisições de IA."""
    prompt: str
    max_tokens: int = 100
    temperature: float = 0.7
    model: str = os.getenv("AI_MODEL_VERSION", "gpt-4")
    additional_params: Dict[str, Any] = {}

class AIResponse(BaseModel):
    """Modelo base para respostas de IA."""
    content: str
    model_used: str
    usage: Dict[str, int]
    raw_response: Dict[str, Any]

class AIProvider(ABC):
    """Interface base para provedores de IA."""
    
    @abstractmethod
    async def generate_text(self, request: AIRequest) -> AIResponse:
        """Gera texto usando o modelo de IA."""
        pass
    
    @abstractmethod
    async def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analisa o sentimento do texto."""
        pass
    
    @abstractmethod
    async def classify_text(self, text: str, categories: List[str]) -> Dict[str, float]:
        """Classifica o texto em categorias."""
        pass

class OpenAIProvider(AIProvider):
    """Implementação do provedor OpenAI."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY não configurada")
        openai.api_key = self.api_key

    @monitor_ai_request(service="openai", model="gpt")
    async def generate_text(self, request: AIRequest) -> AIResponse:
        """Gera texto usando o modelo OpenAI."""
        try:
            response = await openai.ChatCompletion.acreate(
                model=request.model,
                messages=[{"role": "user", "content": request.prompt}],
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                **request.additional_params
            )
            
            return AIResponse(
                content=response.choices[0].message.content,
                model_used=response.model,
                usage=response.usage,
                raw_response=response
            )
        except Exception as e:
            logger.error(f"Erro na geração de texto OpenAI: {str(e)}")
            raise

    @monitor_ai_request(service="openai", model="sentiment")
    async def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analisa o sentimento do texto usando OpenAI."""
        prompt = f"Analise o sentimento do seguinte texto e retorne um score de -1 (muito negativo) a 1 (muito positivo): {text}"
        
        try:
            response = await self.generate_text(AIRequest(prompt=prompt, max_tokens=50))
            # Processar a resposta para extrair o score
            # Isso é uma simplificação, você pode melhorar o parsing
            score = float(response.content.strip())
            return {"score": max(-1, min(1, score))}
        except Exception as e:
            logger.error(f"Erro na análise de sentimento: {str(e)}")
            raise

    @monitor_ai_request(service="openai", model="classification")
    async def classify_text(self, text: str, categories: List[str]) -> Dict[str, float]:
        """Classifica o texto em categorias usando OpenAI."""
        categories_str = ", ".join(categories)
        prompt = f"Classifique o seguinte texto nas categorias ({categories_str}). Retorne as probabilidades para cada categoria: {text}"
        
        try:
            response = await self.generate_text(AIRequest(prompt=prompt, max_tokens=100))
            # Processar a resposta para extrair as probabilidades
            # Isso é uma simplificação, você pode melhorar o parsing
            probabilities = {}
            for category in categories:
                # Implementar lógica de parsing mais robusta aqui
                probabilities[category] = 0.0
            return probabilities
        except Exception as e:
            logger.error(f"Erro na classificação de texto: {str(e)}")
            raise

class AIFactory:
    """Fábrica para criar instâncias de provedores de IA."""
    
    @staticmethod
    def create_provider(provider_name: str = "openai") -> AIProvider:
        """Cria uma instância do provedor de IA especificado."""
        providers = {
            "openai": OpenAIProvider,
            # Adicionar outros provedores aqui
        }
        
        provider_class = providers.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Provedor de IA não suportado: {provider_name}")
        
        return provider_class() 