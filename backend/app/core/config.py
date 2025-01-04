"""
Configurações da aplicação
"""

from typing import Any, Dict, List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator, ConfigDict
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    model_config = ConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="allow"  # Permite campos extras do .env
    )

    # Application
    PROJECT_NAME: str = "AI Agency"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DESCRIPTION: str = "AI Agency API - Plataforma de Serviços de IA"
    DEBUG: bool = True
    TESTING: bool = True
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "app"
    USE_SQLITE: bool = True
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./app.db"
    )
    
    # SQLAlchemy Configuration
    SQLALCHEMY_POOL_SIZE: int = 20
    SQLALCHEMY_MAX_OVERFLOW: int = 30
    SQLALCHEMY_POOL_TIMEOUT: int = 60
    SQLALCHEMY_POOL_RECYCLE: int = 1800  # 30 minutos
    SQLALCHEMY_POOL_PRE_PING: bool = True
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ECHO: bool = False
    
    # SQLAlchemy Engine Options
    @property
    def SQLALCHEMY_ENGINE_OPTIONS(self) -> Dict[str, Any]:
        """
        Retorna as opções do engine do SQLAlchemy baseado no tipo de banco
        """
        if self.USE_SQLITE:
            return {
                "connect_args": {
                    "check_same_thread": False,
                    "timeout": 30
                }
            }
        return {
            "pool_pre_ping": True,
            "pool_size": self.SQLALCHEMY_POOL_SIZE,
            "max_overflow": self.SQLALCHEMY_MAX_OVERFLOW,
            "pool_timeout": self.SQLALCHEMY_POOL_TIMEOUT,
            "pool_recycle": self.SQLALCHEMY_POOL_RECYCLE,
        }
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    JWT_SECRET_KEY: str = "your-super-secret-key-here"
    JWT_REFRESH_SECRET_KEY: str = "your-super-secret-refresh-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days
    ALGORITHM: str = "HS256"  # Algoritmo para JWT
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "5000"))  # Aumentado para testes
    RATE_LIMIT_PER_SECOND: int = 500  # Aumentado para testes
    RATE_LIMIT_BURST: int = 200  # Aumentado para testes
    RATE_LIMIT_REQUESTS: int = 10000  # Aumentado para testes
    RATE_LIMIT_PERIOD: int = 60  # 1 minuto
    RATE_LIMIT_BURST_PERIOD: int = 5  # Aumentado para 5 segundos
    
    # Token Bucket Configuration
    TOKEN_BUCKET_ENABLED: bool = True
    TOKEN_BUCKET_CAPACITY: int = 2000  # Aumentado para testes
    TOKEN_BUCKET_REFILL_RATE: float = 200.0  # Aumentado para testes
    TOKEN_BUCKET_BURST_CAPACITY: int = 1000  # Aumentado para testes
    TOKEN_BUCKET_BURST_REFILL_RATE: float = 400.0  # Aumentado para testes
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    REDIS_POOL_SIZE: int = int(os.getenv("REDIS_POOL_SIZE", "50"))  # Aumentado para testes
    REDIS_RETRY_ATTEMPTS: int = int(os.getenv("REDIS_RETRY_ATTEMPTS", "3"))
    REDIS_RETRY_DELAY: int = int(os.getenv("REDIS_RETRY_DELAY", "1"))
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    COHERE_API_KEY: Optional[str] = os.getenv("COHERE_API_KEY")
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    AZURE_API_KEY: Optional[str] = os.getenv("AZURE_API_KEY")
    HUGGINGFACE_API_KEY: Optional[str] = os.getenv("HUGGINGFACE_API_KEY")
    
    # API Configuration
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    ANTHROPIC_API_BASE: str = "https://api.anthropic.com"
    COHERE_API_BASE: str = "https://api.cohere.ai"
    GOOGLE_API_BASE: str = "https://generativelanguage.googleapis.com"
    AZURE_API_BASE: str = os.getenv("AZURE_API_BASE", "")
    HUGGINGFACE_API_BASE: str = "https://api-inference.huggingface.co"
    
    # Model Configuration
    DEFAULT_MODEL: str = "gpt-3.5-turbo"
    OPENAI_MODELS: List[str] = ["gpt-3.5-turbo", "gpt-4"]
    ANTHROPIC_MODELS: List[str] = ["claude-2", "claude-instant-1"]
    COHERE_MODELS: List[str] = ["command", "command-light"]
    GOOGLE_MODELS: List[str] = ["palm-2"]
    AZURE_MODELS: List[str] = []
    HUGGINGFACE_MODELS: List[str] = []
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_UPDATE_INTERVAL_SECONDS: int = 30
    
    # Agents Configuration
    DEFAULT_AGENT_TIMEOUT: int = 30  # seconds
    MAX_CONCURRENT_TASKS: int = 10
    CONTEXT_RETENTION_HOURS: int = 24
    
    # Email/SMTP Configuration
    SMTP_HOST: str = ""  # Vazio desabilita o serviço de email
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_FROM_EMAIL: str = "noreply@aiagency.com"
    SMTP_FROM_NAME: str = "AI Agency"
    
    # Slack Configuration
    SLACK_WEBHOOK_URL: str = ""  # Vazio desabilita as notificações do Slack
    SLACK_CHANNEL: str = "#monitoring"
    SLACK_USERNAME: str = "AI Agency Bot"
    SLACK_ICON_EMOJI: str = ":robot_face:"
    SLACK_ENABLED: bool = False
    
    # Circuit Breaker Configuration
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 10  # Aumentado
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 30  # Reduzido
    CIRCUIT_BREAKER_RESET_TIMEOUT: int = 300
    CIRCUIT_BREAKER_MAX_FAILURES: int = 20  # Aumentado
    CIRCUIT_BREAKER_ENABLED: bool = True

settings = Settings()

def get_settings() -> Settings:
    return settings 