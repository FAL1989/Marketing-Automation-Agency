from typing import Optional, Dict, Any
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

class ModelConfig(BaseModel):
    """Configuração de um modelo específico"""
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 2000
    stop_sequences: Optional[list[str]] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    top_p: Optional[float] = None

class ProviderConfig(BaseModel):
    """Configuração de um provedor de IA"""
    api_key: str
    organization_id: Optional[str] = None
    default_model: str
    models: Dict[str, ModelConfig]

class AIConfigService:
    """Serviço para gerenciar configurações dos provedores de IA"""
    
    def __init__(self):
        self.providers = {
            "openai": ProviderConfig(
                api_key=os.getenv("OPENAI_API_KEY", ""),
                organization_id=os.getenv("OPENAI_ORG_ID"),
                default_model="gpt-3.5-turbo",
                models={
                    "gpt-3.5-turbo": ModelConfig(
                        model_name="gpt-3.5-turbo",
                        temperature=0.7,
                        max_tokens=2000
                    ),
                    "gpt-4": ModelConfig(
                        model_name="gpt-4",
                        temperature=0.7,
                        max_tokens=4000
                    )
                }
            ),
            "anthropic": ProviderConfig(
                api_key=os.getenv("ANTHROPIC_API_KEY", ""),
                default_model="claude-2",
                models={
                    "claude-2": ModelConfig(
                        model_name="claude-2",
                        temperature=0.7,
                        max_tokens=4000
                    )
                }
            ),
            "cohere": ProviderConfig(
                api_key=os.getenv("COHERE_API_KEY", ""),
                default_model="command",
                models={
                    "command": ModelConfig(
                        model_name="command",
                        temperature=0.7,
                        max_tokens=2000
                    )
                }
            )
        }
    
    def get_provider_config(self, provider: str) -> ProviderConfig:
        """Retorna a configuração de um provedor específico"""
        if provider not in self.providers:
            raise ValueError(f"Provedor {provider} não encontrado")
        return self.providers[provider]
    
    def get_model_config(
        self,
        provider: str,
        model_name: Optional[str] = None
    ) -> ModelConfig:
        """
        Retorna a configuração de um modelo específico.
        Se model_name não for fornecido, retorna o modelo padrão do provedor.
        """
        provider_config = self.get_provider_config(provider)
        
        if not model_name:
            model_name = provider_config.default_model
            
        if model_name not in provider_config.models:
            raise ValueError(
                f"Modelo {model_name} não encontrado para o provedor {provider}"
            )
            
        return provider_config.models[model_name]
    
    def update_model_config(
        self,
        provider: str,
        model_name: str,
        config: Dict[str, Any]
    ) -> None:
        """Atualiza a configuração de um modelo específico"""
        provider_config = self.get_provider_config(provider)
        
        if model_name not in provider_config.models:
            raise ValueError(
                f"Modelo {model_name} não encontrado para o provedor {provider}"
            )
            
        current_config = provider_config.models[model_name]
        for key, value in config.items():
            if hasattr(current_config, key):
                setattr(current_config, key, value)
            else:
                raise ValueError(f"Configuração inválida: {key}")
                
    def add_model_config(
        self,
        provider: str,
        model_name: str,
        config: ModelConfig
    ) -> None:
        """Adiciona um novo modelo à configuração do provedor"""
        provider_config = self.get_provider_config(provider)
        provider_config.models[model_name] = config