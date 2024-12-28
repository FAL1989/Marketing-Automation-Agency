from pydantic_settings import BaseSettings
from typing import Dict, Any, Optional

class Settings(BaseSettings):
    # Configurações da Aplicação
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Chaves de API dos Provedores
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str
    COHERE_API_KEY: str
    
    # Configurações do Redis
    REDIS_URL: str
    
    # Configurações do RabbitMQ
    RABBITMQ_URL: str
    
    # Configurações de Rate Limiting
    RATE_LIMIT_TOKENS_PER_MIN: int = 100000  # Tokens por minuto
    RATE_LIMIT_REQUESTS_PER_MIN: int = 1000   # Requisições por minuto
    
    # Configurações dos Modelos
    MODEL_CONFIGS: Dict[str, Any] = {
        "openai": {
            "default_model": "gpt-4",
            "fallback_model": "gpt-3.5-turbo",
            "max_tokens": 4000,
            "temperature": 0.7
        },
        "anthropic": {
            "default_model": "claude-2",
            "fallback_model": "claude-instant-1",
            "max_tokens": 4000,
            "temperature": 0.7
        },
        "cohere": {
            "default_model": "command",
            "fallback_model": "command-light",
            "max_tokens": 2000,
            "temperature": 0.7
        }
    }
    
    # Configurações de Cache
    CACHE_TTL: int = 3600  # 1 hora para respostas geradas
    CACHE_ENABLED: bool = True
    
    # Configurações de Retry
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0  # segundos
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 