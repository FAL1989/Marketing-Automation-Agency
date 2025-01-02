import logging
from typing import Optional
import redis.asyncio as redis
from app.core.redis_config import get_redis_config, get_redis_url

logger = logging.getLogger(__name__)

# Cliente Redis global
redis_client: Optional[redis.Redis] = None

async def init_redis_pool() -> redis.Redis:
    """
    Inicializa o pool de conexões Redis
    """
    global redis_client
    
    try:
        if redis_client is not None:
            logger.info("Usando conexão Redis existente")
            return redis_client
            
        logger.info("Inicializando nova conexão Redis")
        config = get_redis_config()
        
        # Inicializa cliente diretamente
        redis_client = redis.Redis(
            host=config["host"],
            port=config["port"],
            db=config["db"],
            password=config["password"],
            decode_responses=True,
            socket_timeout=config["socket_timeout"],
            socket_connect_timeout=config["socket_connect_timeout"]
        )
        
        # Testa conexão
        await redis_client.ping()
        logger.info("Conexão Redis estabelecida com sucesso")
        
        return redis_client
        
    except Exception as e:
        logger.error(f"Erro ao inicializar Redis: {str(e)}")
        raise

async def get_redis() -> redis.Redis:
    """
    Retorna cliente Redis, inicializando se necessário
    """
    global redis_client
    
    if redis_client is None:
        redis_client = await init_redis_pool()
    
    return redis_client

async def close_redis_connection():
    """
    Fecha conexão com Redis
    """
    global redis_client
    
    if redis_client is not None:
        logger.info("Fechando conexão Redis")
        await redis_client.close()
        redis_client = None

async def check_redis_health() -> bool:
    """
    Verifica saúde da conexão Redis
    """
    try:
        client = await get_redis()
        await client.ping()
        return True
    except Exception as e:
        logger.error(f"Erro ao verificar saúde do Redis: {str(e)}")
        return False

async def clear_redis_data():
    """
    Limpa todos os dados do Redis (usar com cautela!)
    """
    try:
        client = await get_redis()
        await client.flushdb()
        logger.info("Dados Redis limpos com sucesso")
    except Exception as e:
        logger.error(f"Erro ao limpar dados Redis: {str(e)}")
        raise

async def get_redis_info() -> dict:
    """
    Retorna informações sobre o servidor Redis
    """
    try:
        client = await get_redis()
        info = await client.info()
        return {
            "version": info.get("redis_version"),
            "used_memory": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
            "uptime": info.get("uptime_in_seconds"),
            "total_commands": info.get("total_commands_processed"),
            "hits": info.get("keyspace_hits", 0),
            "misses": info.get("keyspace_misses", 0),
            "keys": {
                db: info.get(f"db{db}", {}).get("keys", 0)
                for db in range(16)
                if f"db{db}" in info
            }
        }
    except Exception as e:
        logger.error(f"Erro ao obter informações Redis: {str(e)}")
        raise 