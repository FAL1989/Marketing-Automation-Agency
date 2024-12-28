from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import ConfigDict

class Settings(BaseSettings):
    # Configurações da Aplicação
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Configurações do Banco de Dados
    DATABASE_URL: str
    
    # Configurações do Redis
    REDIS_URL: str
    
    # Configurações do RabbitMQ
    RABBITMQ_URL: str
    
    # Configurações do Auth Service
    AUTH_SERVICE_URL: str = "http://auth-service:8000"
    AUTH_SERVICE_TIMEOUT: float = 5.0  # segundos
    
    # Configurações de Cache
    CACHE_TTL: int = 3600  # 1 hora
    CACHE_ENABLED: bool = True
    
    # Configurações da OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
        validate_default=True
    )

settings = Settings() 