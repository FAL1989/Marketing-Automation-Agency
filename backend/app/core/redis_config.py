from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
from .config import settings
import os

# Configuração de retry mais robusta
REDIS_RETRY = Retry(
    ExponentialBackoff(cap=5, base=1.5),  # Backoff mais suave
    retries=5,  # Mais tentativas
    supported_errors=(
        Exception  # Captura qualquer erro
    )
)

# Configurações padrão do Redis
REDIS_CONFIG = {
    "url": "redis://localhost:6379/1" if os.getenv("TESTING", "").lower() == "true" else settings.REDIS_URL,
    "decode_responses": True,
    "socket_timeout": 5.0,
    "socket_connect_timeout": 5.0,
    "retry_on_timeout": True,
    "health_check_interval": 30,
    "max_connections": 100
} 