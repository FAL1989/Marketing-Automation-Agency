import os
import logging
import openai
from typing import Dict, Any, Optional
from app.services.providers.base_provider import BaseProvider

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseProvider):
    def __init__(self):
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            openai.api_key = api_key
        except Exception as e:
            logger.error(f"Error initializing OpenAI provider: {str(e)}")
            raise

    async def generate_content(self, prompt: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        try:
            params = parameters or {}
            response = openai.ChatCompletion.create(
                model=params.get("model", "gpt-3.5-turbo"),
                messages=[
                    {"role": "system", "content": "Você é um assistente prestativo especializado em gerar conteúdo de alta qualidade em português."},
                    {"role": "user", "content": prompt}
                ],
                **{k: v for k, v in params.items() if k != "model"}
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating content with OpenAI: {str(e)}")
            raise 