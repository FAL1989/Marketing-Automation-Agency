from typing import List
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any
import os

class Settings(BaseSettings):
    # Configurações básicas
    PROJECT_NAME: str = "AI Agency"
    API_V1_STR: str = "/api/v1"
    
    # Configurações de banco de dados
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/aiagency")
    
    # Configurações de autenticação
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 dias
    
    # Configurações do AI Orchestrator
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    COHERE_API_KEY: Optional[str] = os.getenv("COHERE_API_KEY")
    
    # Cache
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 3600  # 1 hora
    CACHE_MAX_SIZE: int = 1000
    
    # Rate Limiting
    RATE_LIMIT_OPENAI: int = 45  # requisições por minuto
    RATE_LIMIT_ANTHROPIC: int = 30
    RATE_LIMIT_COHERE: int = 20
    
    # Providers
    DEFAULT_PROVIDER: str = "openai"
    DEFAULT_MODEL: str = "gpt-3.5-turbo"
    
    # ClickHouse
    CLICKHOUSE_URL: str = os.getenv("CLICKHOUSE_URL", "http://localhost:8123")
    CLICKHOUSE_USER: str = os.getenv("CLICKHOUSE_USER", "default")
    CLICKHOUSE_PASSWORD: str = os.getenv("CLICKHOUSE_PASSWORD", "")
    CLICKHOUSE_DB: str = os.getenv("CLICKHOUSE_DB", "default")
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 