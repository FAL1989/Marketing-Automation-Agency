from typing import Optional
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # AI Providers
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
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 