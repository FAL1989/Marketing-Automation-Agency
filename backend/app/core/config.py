"""
Configurações da aplicação
"""

import os
import logging
from functools import lru_cache
from typing import Any, Dict, Optional
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """
    Configurações da aplicação
    """
    # Ambiente
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SQL_DEBUG: bool = False
    
    # Aplicação
    PROJECT_NAME: str = "AI Agency API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Segurança
    SECRET_KEY: str = "your-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 dias
    ALGORITHM: str = "HS256"
    
    # Banco de dados
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    
    # Configurações do Pool SQLAlchemy
    SQLALCHEMY_POOL_SIZE: int = 20  # Aumentado para suportar mais conexões simultâneas
    SQLALCHEMY_MAX_OVERFLOW: int = 10  # Conexões adicionais permitidas além do pool_size
    SQLALCHEMY_POOL_TIMEOUT: int = 30  # Tempo máximo de espera por uma conexão
    SQLALCHEMY_POOL_RECYCLE: int = 1800  # Recicla conexões após 30 minutos
    SQLALCHEMY_POOL_PRE_PING: bool = True  # Verifica conexões antes de usar
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_POOL_SIZE: int = 20  # Aumentado para melhor throughput
    REDIS_MAX_CONNECTIONS: int = 100  # Aumentado limite máximo
    REDIS_TIMEOUT: int = 5
    REDIS_RETRY_ON_TIMEOUT: bool = True
    REDIS_RETRY_MAX_ATTEMPTS: int = 3
    REDIS_RETRY_DELAY: float = 0.1  # Delay entre tentativas em segundos
    REDIS_HEALTH_CHECK_INTERVAL: int = 30  # Intervalo de health check em segundos
    
    # Cache
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 300  # 5 minutos
    CACHE_PREFIX: str = "cache:"
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 3600
    RATE_LIMIT_BURST: int = 50
    RATE_LIMIT_BURST_PERIOD: int = 1
    
    # Token Bucket Config
    TOKEN_BUCKET_ENABLED: bool = True
    TOKEN_BUCKET_CAPACITY: int = 100
    TOKEN_BUCKET_REFILL_RATE: float = 1.0  # tokens por segundo
    TOKEN_BUCKET_BURST_CAPACITY: int = 50
    TOKEN_BUCKET_BURST_REFILL_RATE: float = 50.0  # tokens por segundo
    
    # Monitoramento
    METRICS_ENABLED: bool = True
    METRICS_PATH: str = "/metrics/"
    METRICS_NAMESPACE: str = "ai_agency"
    
    # RabbitMQ
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    
    # Grafana
    GRAFANA_ADMIN_USER: str = "admin"
    GRAFANA_ADMIN_PASSWORD: str = "admin"
    
    # APIs Externas
    OPENAI_API_KEY: str = "your_openai_key"
    ANTHROPIC_API_KEY: str = "your_anthropic_key"
    COHERE_API_KEY: str = "your_cohere_key"
    
    # Configurações de Log
    LOG_DIR: str = "logs"
    LOG_FILE: str = "app.log"
    LOG_PATH: str = os.path.join(LOG_DIR, LOG_FILE)
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    
    # Email/SMTP
    SMTP_HOST: str = ""  # Vazio desabilita o serviço de email
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_FROM_EMAIL: str = "noreply@aiagency.com"
    SMTP_FROM_NAME: str = "AI Agency"
    
    # Slack
    SLACK_WEBHOOK_URL: str = ""  # Vazio desabilita as notificações do Slack
    SLACK_CHANNEL: str = "#monitoring"
    SLACK_USERNAME: str = "AI Agency Bot"
    SLACK_ICON_EMOJI: str = ":robot_face:"
    SLACK_ENABLED: bool = False
    
    # Circuit Breaker
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5  # Número de falhas antes de abrir o circuito
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60  # Tempo em segundos para tentar recuperar
    CIRCUIT_BREAKER_RESET_TIMEOUT: int = 300  # Tempo em segundos para resetar o contador de falhas
    CIRCUIT_BREAKER_MAX_FAILURES: int = 10  # Máximo de falhas permitidas antes de bloquear completamente
    CIRCUIT_BREAKER_ENABLED: bool = True  # Habilita/desabilita o circuit breaker
    
    def configure_logging(self) -> None:
        """
        Configura o logging da aplicação
        """
        # Cria o diretório de logs se não existir
        os.makedirs(self.LOG_DIR, exist_ok=True)
        
        # Configuração básica
        logging.basicConfig(
            level=getattr(logging, self.LOG_LEVEL),
            format=self.LOG_FORMAT,
            datefmt=self.LOG_DATE_FORMAT,
            handlers=[
                logging.FileHandler(self.LOG_PATH),
                logging.StreamHandler()
            ]
        )
        
        # Reduz logging de bibliotecas
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
        logging.getLogger("aioredis").setLevel(logging.WARNING)
        
        if self.DEBUG:
            logging.getLogger("app").setLevel(logging.DEBUG)
            
            if self.SQL_DEBUG:
                logging.getLogger("sqlalchemy").setLevel(logging.DEBUG)
                
        logger.info(f"Configurações carregadas para ambiente: {self.ENVIRONMENT}")

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "allow"
        protected_namespaces = ()
        
# Instância global das configurações
settings = Settings()

# Configura logging
settings.configure_logging()

@lru_cache()
def get_settings() -> Settings:
    """
    Retorna instância das configurações com cache
    """
    return Settings() 