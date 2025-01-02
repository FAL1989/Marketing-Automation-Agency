from typing import Dict, Any
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_redis_config() -> Dict[str, Any]:
    """
    Retorna a configuração do Redis baseada nas configurações do ambiente
    """
    config = {
        # Configurações básicas
        "host": settings.REDIS_HOST,
        "port": settings.REDIS_PORT,
        "db": settings.REDIS_DB,
        "password": settings.REDIS_PASSWORD,
        "decode_responses": True,
        
        # Pool de conexões
        "max_connections": 50,
        
        # Timeouts
        "socket_timeout": 30,
        "socket_connect_timeout": 30,
        "retry_on_timeout": True
    }
    
    # Ajusta configurações baseado no ambiente
    if settings.ENVIRONMENT == "development":
        config.update({
            "max_connections": 10,
            "socket_timeout": 60,
            "socket_connect_timeout": 30
        })
    elif settings.ENVIRONMENT == "testing":
        config.update({
            "max_connections": 5,
            "socket_timeout": 5,
            "socket_connect_timeout": 5
        })
    
    logger.info("Configuração Redis carregada para ambiente: %s", settings.ENVIRONMENT)
    return config

def get_redis_url() -> str:
    """
    Retorna a URL de conexão do Redis formatada
    """
    config = get_redis_config()
    auth = f":{config['password']}" if config['password'] else ""
    return f"redis://{auth}@{config['host']}:{config['port']}/{config['db']}"

async def configure_redis(redis_client) -> bool:
    """
    Configura o Redis com as configurações otimizadas
    """
    try:
        config = get_redis_config()
        
        # Aplica configurações
        for key, value in config.items():
            if key in ["max_memory", "maxmemory_policy"]:
                await redis_client.config_set(key, value)
        
        logger.info("Redis configurado com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao configurar Redis: {str(e)}")
        return False 