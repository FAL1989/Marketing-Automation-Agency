from typing import Dict, Any, Optional
import anthropic
import logging
from ..ai_config_service import AIConfigService, ModelConfig

logger = logging.getLogger(__name__)

class AnthropicProvider:
    def __init__(self, config_service: AIConfigService):
        self.config_service = config_service
        self.provider_config = config_service.get_provider_config("anthropic")
        self.client = anthropic.Anthropic(api_key=self.provider_config.api_key)
    
    async def generate(
        self,
        prompt: str,
        variables: Dict[str, Any],
        model_name: Optional[str] = None
    ) -> str:
        """
        Gera conteúdo usando a API da Anthropic.
        
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
                "anthropic",
                model_name
            )
            
            # Prepara o prompt com as variáveis
            formatted_prompt = self._format_prompt(prompt, variables)
            
            # Faz a chamada para a API
            response = await self._make_api_call(formatted_prompt, model_config)
            
            return response
            
        except Exception as e:
            logger.error(f"Erro ao gerar conteúdo com Anthropic: {str(e)}")
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
        """Faz a chamada para a API da Anthropic"""
        try:
            # Prepara os parâmetros da chamada
            params = {
                "model": model_config.model_name,
                "max_tokens": model_config.max_tokens,
                "temperature": model_config.temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": formatted_prompt
                    }
                ]
            }
            
            # Adiciona parâmetros opcionais se definidos
            if model_config.stop_sequences:
                params["stop_sequences"] = model_config.stop_sequences
            if model_config.top_p is not None:
                params["top_p"] = model_config.top_p
            
            # Faz a chamada para a API
            response = await self.client.messages.create(**params)
            
            # Extrai e retorna o conteúdo gerado
            return response.content[0].text
            
        except anthropic.RateLimitError:
            raise Exception("Limite de requisições atingido")
        except anthropic.AuthenticationError:
            raise Exception("Erro de autenticação com a API")
        except anthropic.APIError as e:
            raise Exception(f"Erro na API da Anthropic: {str(e)}")
        except Exception as e:
            raise Exception(f"Erro inesperado: {str(e)}")
    
    async def validate_api_key(self) -> bool:
        """Valida se a API key está funcionando"""
        try:
            # Tenta fazer uma chamada simples para validar a key
            await self.client.messages.create(
                model="claude-2",
                max_tokens=10,
                messages=[{"role": "user", "content": "Olá"}]
            )
            return True
        except:
            return False
    
    async def get_available_models(self) -> list[str]:
        """Retorna a lista de modelos disponíveis"""
        # A Anthropic não tem um endpoint para listar modelos
        # Retornamos os modelos que sabemos que existem
        return ["claude-2", "claude-instant-1"]
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estima o número de tokens em um texto.
        Esta é uma estimativa aproximada, pois o número real
        depende do tokenizador específico do modelo.
        """
        # Estimativa aproximada: 1 token ~= 4 caracteres em inglês
        return len(text) // 4 