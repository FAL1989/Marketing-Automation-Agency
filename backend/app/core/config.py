"""
Configurações da aplicação
"""

import os
import secrets
from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, EmailStr, PostgresDsn, validator
from pydantic_settings import BaseSettings
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """
    Configurações da aplicação usando Pydantic BaseSettings
    """
    # Informações do projeto
    PROJECT_NAME: str = "AI Agency"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "AI Agency API - Plataforma de Serviços de IA"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Ambiente
    TESTING: bool = False
    DEBUG: bool = False
    
    # Database
    USE_SQLITE: bool = False
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "app"
    POSTGRES_PORT: int = 5432
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    # Pool settings
    SQLALCHEMY_POOL_SIZE: int = 5
    SQLALCHEMY_MAX_OVERFLOW: int = 10
    SQLALCHEMY_POOL_TIMEOUT: int = 30
    
    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        """
        Monta a string de conexão com o banco de dados
        """
        if v:
            return v
            
        if values.get("USE_SQLITE"):
            logger.info("Usando SQLite para testes")
            return "sqlite+aiosqlite:///./test.db"
            
        try:
            port = int(values.get("POSTGRES_PORT", 5432))
            return PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=values.get("POSTGRES_USER"),
                password=values.get("POSTGRES_PASSWORD"),
                host=values.get("POSTGRES_SERVER"),
                port=port,
                path=f"/{values.get('POSTGRES_DB') or ''}",
            ).unicode_string()
        except Exception as e:
            logger.error(f"Erro ao montar string de conexão: {e}")
            raise
            
    @property
    def SQLALCHEMY_ENGINE_OPTIONS(self) -> Dict[str, Any]:
        """
        Opções do engine SQLAlchemy
        """
        if self.USE_SQLITE:
            return {
                "echo": self.DEBUG,
                "future": True
            }
            
        return {
            "echo": self.DEBUG,
            "future": True,
            "pool_size": self.SQLALCHEMY_POOL_SIZE,
            "max_overflow": self.SQLALCHEMY_MAX_OVERFLOW,
            "pool_timeout": self.SQLALCHEMY_POOL_TIMEOUT
        }
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_RATELIMIT_DB: int = 1
    REDIS_URL: Optional[str] = None
    
    @validator("REDIS_URL", pre=True)
    def assemble_redis_connection(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        """
        Monta a URL de conexão com o Redis
        """
        if v:
            return v
            
        try:
            port = int(values.get("REDIS_PORT", 6379))
            return f"redis://{values.get('REDIS_HOST')}:{port}/{values.get('REDIS_DB')}"
        except Exception as e:
            logger.error(f"Erro ao montar URL do Redis: {e}")
            raise
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_REFRESH_SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_MAX_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # 60 segundos
    RATE_LIMIT_PER_MINUTE: int = 60  # 60 requisições por minuto
    RATE_LIMIT_PER_SECOND: int = 1  # 1 requisição por segundo
    RATE_LIMIT_BURST: int = 5
    RATE_LIMIT_EXCLUDE_PATHS: List[str] = ["/api/v1/health", "/metrics"]
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Metrics
    METRICS_PORT: int = 9090
    
    # SMTP Settings
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: EmailStr = "noreply@example.com"
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_USE_CREDENTIALS: bool = True
    SMTP_VALIDATE_CERTS: bool = True
    
    # Slack Settings
    SLACK_WEBHOOK_URL: str = ""
    SLACK_CHANNEL: str = "#monitoring"
    SLACK_USERNAME: str = "AI Agency Bot"
    SLACK_ICON_EMOJI: str = ":robot_face:"
    SLACK_ENABLED: bool = False
    
    # Circuit Breaker Settings
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RESET_TIMEOUT: int = 60
    CIRCUIT_BREAKER_MAX_FAILURES: int = 3
    CIRCUIT_BREAKER_RETRY_TIME: int = 30
    CIRCUIT_BREAKER_EXCLUDE_PATHS: List[str] = ["/api/v1/health", "/metrics"]
    
    # API Key Settings
    API_KEY: str = secrets.token_urlsafe(32)
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "allow"  # Permite campos extras

@lru_cache()
def get_settings() -> Settings:
    """
    Retorna as configurações da aplicação.
    Em ambiente de teste, retorna as configurações de teste.
    """
    if os.getenv("TESTING", "").lower() == "true":
        try:
            from tests.conftest import test_settings
            return test_settings
        except ImportError:
            pass
    return Settings()

settings = get_settings() 