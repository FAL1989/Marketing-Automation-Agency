from typing import Dict, Any, Optional
import cohere
import logging
from ..ai_config_service import AIConfigService, ModelConfig

logger = logging.getLogger(__name__)

class CohereProvider:
    def __init__(self, config_service: AIConfigService):
        self.config_service = config_service
        self.provider_config = config_service.get_provider_config("cohere")
        self.client = cohere.Client(api_key=self.provider_config.api_key)
    
    async def generate(
        self,
        prompt: str,
        variables: Dict[str, Any],
        model_name: Optional[str] = None
    ) -> str:
        """
        Gera conteúdo usando a API da Cohere.
        
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
            # Obtém configuração do modelo
            model_config = self.config_service.get_model_config(
                "cohere",
                model_name
            )
            
            # Prepara o prompt com as variáveis
            formatted_prompt = self._format_prompt(prompt, variables)
            
            # Faz a chamada para a API
            response = await self._make_api_call(formatted_prompt, model_config)
            
            return response
            
        except Exception as e:
            logger.error(f"Erro ao gerar conteúdo com Cohere: {str(e)}")
            raise
    
    def _format_prompt(self, prompt: str, variables: Dict[str, Any]) -> str:
        """Formata o prompt substituindo as variáveis"""
        try:
            return prompt.format(**variables)
        except KeyError as e:
            raise ValueError(f"Variável {e} não encontrada no prompt")
        except Exception as e:
            raise ValueError(f"Erro ao formatar prompt: {str(e)}")
    
    async def _make_api_call(
        self,
        formatted_prompt: str,
        model_config: ModelConfig
    ) -> str:
        """Faz a chamada para a API da Cohere"""
        try:
            # Prepara os parâmetros da chamada
            params = {
                "model": model_config.model_name,
                "prompt": formatted_prompt,
                "max_tokens": model_config.max_tokens,
                "temperature": model_config.temperature
            }
            
            # Adiciona parâmetros opcionais se definidos
            if model_config.stop_sequences:
                params["stop_sequences"] = model_config.stop_sequences
            if model_config.frequency_penalty is not None:
                params["frequency_penalty"] = model_config.frequency_penalty
            if model_config.presence_penalty is not None:
                params["presence_penalty"] = model_config.presence_penalty
            if model_config.top_p is not None:
                params["p"] = model_config.top_p
            
            # Faz a chamada para a API
            response = await self.client.generate(**params)
            
            # Extrai e retorna o conteúdo gerado
            return response.generations[0].text.strip()
            
        except cohere.error.CohereError as e:
            if "rate limit" in str(e).lower():
                raise Exception("Limite de requisições atingido")
            elif "unauthorized" in str(e).lower():
                raise Exception("Erro de autenticação com a API")
            else:
                raise Exception(f"Erro na API da Cohere: {str(e)}")
        except Exception as e:
            raise Exception(f"Erro inesperado: {str(e)}")
    
    async def validate_api_key(self) -> bool:
        """Valida se a API key está funcionando"""
        try:
            # Tenta fazer uma chamada simples para validar a key
            await self.client.generate(
                model="command",
                prompt="Olá",
                max_tokens=10
            )
            return True
        except:
            return False
    
    async def get_available_models(self) -> list[str]:
        """Retorna a lista de modelos disponíveis"""
        try:
            models = await self.client.list_models()
            return [model.id for model in models]
        except Exception as e:
            logger.error(f"Erro ao obter modelos disponíveis: {str(e)}")
            return ["command", "command-light", "command-nightly"]
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estima o número de tokens em um texto.
        Esta é uma estimativa aproximada, pois o número real
        depende do tokenizador específico do modelo.
        """
        # Estimativa aproximada: 1 token ~= 4 caracteres em inglês
        return len(text) // 4 