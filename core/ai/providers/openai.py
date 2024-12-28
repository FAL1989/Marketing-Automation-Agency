from typing import Optional, Dict, Any
import openai
from ..base import AIProvider
from ...config import settings

class OpenAIProvider(AIProvider):
    def __init__(self):
        super().__init__()
        openai.api_key = settings.OPENAI_API_KEY
        self.last_token_count = 0
        self.last_cost = 0.0

    async def generate(self, prompt: str, **kwargs) -> str:
        try:
            model = kwargs.get("model", settings.DEFAULT_MODEL)
            response = await openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Você é um assistente especializado em gerar conteúdo de alta qualidade em português."},
                    {"role": "user", "content": prompt}
                ],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2000),
                top_p=kwargs.get("top_p", 1),
                frequency_penalty=kwargs.get("frequency_penalty", 0),
                presence_penalty=kwargs.get("presence_penalty", 0)
            )
            
            self.last_token_count = response.usage.total_tokens
            self.last_cost = float(response.usage.total_tokens) * 0.002 / 1000  # Estimativa básica de custo
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.last_token_count = 0
            self.last_cost = 0.0
            raise Exception(f"Erro ao gerar conteúdo com OpenAI: {str(e)}") 