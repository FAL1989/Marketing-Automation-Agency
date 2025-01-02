import openai
from typing import Optional, Dict, Any, List
from ..base import AIProvider, AIRequest, AIResponse
from app.core.config import settings
from ...monitoring.metrics import monitor_ai_request

class OpenAIProvider(AIProvider):
    def __init__(self):
        super().__init__()
        openai.api_key = settings.OPENAI_API_KEY
        self.last_token_count = 0
        self.last_cost = 0.0

    @monitor_ai_request(service="openai", model="gpt")
    async def generate_text(self, request: AIRequest) -> AIResponse:
        try:
            response = await openai.ChatCompletion.create(
                model=request.model,
                messages=[
                    {"role": "system", "content": "Você é um assistente especializado em gerar conteúdo de alta qualidade em português."},
                    {"role": "user", "content": request.prompt}
                ],
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                **request.additional_params
            )
            
            self.last_token_count = response.usage.total_tokens
            self.last_cost = float(response.usage.total_tokens) * 0.002 / 1000  # Estimativa básica de custo
            
            return AIResponse(
                content=response.choices[0].message.content,
                model_used=request.model,
                usage={
                    "total_tokens": response.usage.total_tokens,
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens
                },
                raw_response=response
            )
            
        except Exception as e:
            self.last_token_count = 0
            self.last_cost = 0.0
            raise Exception(f"Erro ao gerar conteúdo com OpenAI: {str(e)}")

    @monitor_ai_request(service="openai", model="sentiment")
    async def analyze_sentiment(self, text: str) -> Dict[str, float]:
        try:
            response = await openai.ChatCompletion.create(
                model=settings.DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": "Analise o sentimento do texto fornecido e retorne um score entre -1 (muito negativo) e 1 (muito positivo)."},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=50
            )
            
            sentiment_score = float(response.choices[0].message.content.strip())
            return {"sentiment": sentiment_score}
            
        except Exception as e:
            raise Exception(f"Erro ao analisar sentimento com OpenAI: {str(e)}")

    @monitor_ai_request(service="openai", model="classification")
    async def classify_text(self, text: str, categories: List[str]) -> Dict[str, float]:
        try:
            categories_str = ", ".join(categories)
            prompt = f"Classifique o texto nas seguintes categorias: {categories_str}. Retorne um score de 0 a 1 para cada categoria."
            
            response = await openai.ChatCompletion.create(
                model=settings.DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=100
            )
            
            # Processa a resposta para extrair os scores
            scores = {}
            for category in categories:
                # Implementação simplificada - em produção, seria necessário um parsing mais robusto
                scores[category] = 0.5  # Score padrão
                
            return scores
            
        except Exception as e:
            raise Exception(f"Erro ao classificar texto com OpenAI: {str(e)}")

    async def generate(self, prompt: str, **kwargs) -> str:
        request = AIRequest(
            prompt=prompt,
            max_tokens=kwargs.get("max_tokens", 2000),
            temperature=kwargs.get("temperature", 0.7),
            model=kwargs.get("model", settings.DEFAULT_MODEL),
            additional_params={
                "top_p": kwargs.get("top_p", 1),
                "frequency_penalty": kwargs.get("frequency_penalty", 0),
                "presence_penalty": kwargs.get("presence_penalty", 0)
            }
        )
        
        response = await self.generate_text(request)
        return response.content 