import os
import logging
import openai
from typing import Dict, Any, Optional
from .base_provider import BaseProvider

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseProvider):
    def __init__(self, config_service):
        """
        Inicializa o provedor OpenAI.
        
        Args:
            config_service: Serviço de configuração que contém as chaves de API
        """
        try:
            api_key = config_service.get_provider_config("openai").api_key
            if not api_key:
                raise ValueError("OpenAI API key not found in configuration")
            openai.api_key = api_key
            self.config_service = config_service
        except Exception as e:
            logger.error(f"Error initializing OpenAI provider: {str(e)}")
            raise

    async def generate(
        self,
        prompt: str,
        variables: Dict[str, Any],
        model_name: Optional[str] = None
    ) -> str:
        """
        Gera conteúdo usando a API da OpenAI.
        
        Args:
            prompt: O prompt base para geração
            variables: Variáveis para substituir no prompt
            model_name: Nome do modelo a ser usado (opcional)
            
        Returns:
            str: O conteúdo gerado
            
        Raises:
            Exception: Se houver erro na geração
        """
        try:
            # Formata o prompt com as variáveis
            formatted_prompt = prompt.format(**variables)
            
            # Obtém configuração do modelo
            model_config = self.config_service.get_model_config(
                "openai",
                model_name
            )
            
            # Faz a chamada para a API
            response = await openai.ChatCompletion.acreate(
                model=model_config.model_name,
                messages=[
                    {"role": "system", "content": "Você é um assistente prestativo especializado em gerar conteúdo de alta qualidade em português."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=model_config.temperature,
                max_tokens=model_config.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating content with OpenAI: {str(e)}")
            raise
            
    async def validate_api_key(self) -> bool:
        """Valida se a API key está funcionando"""
        try:
            # Tenta fazer uma chamada simples para validar a key
            await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Olá"}],
                max_tokens=10
            )
            return True
        except:
            return False 