from pydantic_settings import BaseSettings
from typing import Dict, Any, Optional

class Settings(BaseSettings):
    # Configurações da Aplicação
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Configurações do ClickHouse
    CLICKHOUSE_URL: str = "http://clickhouse:8123"
    
    # Configurações do Redis
    REDIS_URL: str
    
    # Configurações do RabbitMQ
    RABBITMQ_URL: str
    
    # Configurações do Auth Service
    AUTH_SERVICE_URL: str = "http://auth-service:8000"
    AUTH_SERVICE_TIMEOUT: float = 5.0  # segundos
    
    # Configurações de Retenção
    METRICS_RETENTION_DAYS: int = 365  # 1 ano
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 