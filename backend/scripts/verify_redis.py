import asyncio
import sys
import logging
from pathlib import Path

# Adiciona o diretório backend ao PYTHONPATH
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from app.core.redis import get_redis, init_redis_pool, close_redis_connection
from app.core.config import settings

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("redis-verify")

async def verify_redis():
    """Verifica a conexão com Redis e suas funcionalidades básicas"""
    try:
        # Inicializa pool de conexões
        logger.info("Inicializando pool de conexões Redis...")
        redis = await init_redis_pool()
        
        # Testa PING
        logger.info("Testando PING...")
        await redis.ping()
        logger.info("✓ PING OK")
        
        # Testa SET/GET
        logger.info("Testando SET/GET...")
        await redis.set("test_key", "test_value", ex=10)
        value = await redis.get("test_key")
        assert value == "test_value"
        logger.info("✓ SET/GET OK")
        
        # Obtém informações do servidor
        logger.info("Obtendo informações do servidor...")
        info = await redis.info()
        logger.info(f"✓ Redis Info: {info}")
        
        # Limpa chave de teste
        await redis.delete("test_key")
        
        logger.info("✅ Todos os testes Redis passaram!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao conectar ao Redis: {str(e)}")
        return False
        
    finally:
        await close_redis_connection()

def main():
    """Função principal"""
    try:
        result = asyncio.run(verify_redis())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("Verificação interrompida pelo usuário")
        sys.exit(1)

if __name__ == "__main__":
    main() 