import asyncio
import sys
import logging
from pathlib import Path

# Adiciona o diretório backend ao PYTHONPATH
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from app.core.redis import redis_manager
from app.core.config import settings

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("redis-check")

async def check_redis_connection():
    """Verifica a conexão com Redis e suas funcionalidades básicas"""
    try:
        # Tenta inicializar o Redis
        logger.info("Inicializando conexão Redis...")
        await redis_manager.initialize()
        
        # Testa operações básicas
        async for redis in redis_manager.get_client():
            # Ping
            logger.info("Testando PING...")
            await redis.ping()
            logger.info("✓ PING OK")
            
            # Set/Get
            logger.info("Testando SET/GET...")
            await redis.set("test_key", "test_value", ex=10)
            value = await redis.get("test_key")
            assert value == "test_value"
            logger.info("✓ SET/GET OK")
            
            # Info
            logger.info("Obtendo informações do servidor...")
            info = await redis_manager.get_info()
            logger.info(f"✓ Redis Info: {info}")
            
            # Limpa chave de teste
            await redis.delete("test_key")
            break  # Só precisamos testar uma vez
            
        logger.info("✅ Todos os testes Redis passaram!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao conectar ao Redis: {str(e)}")
        logger.error(f"URL Redis configurada: {settings.REDIS_URL}")
        return False
    finally:
        await redis_manager.close()

def main():
    """Função principal"""
    try:
        result = asyncio.run(check_redis_connection())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("Verificação interrompida pelo usuário")
        sys.exit(1)

if __name__ == "__main__":
    main() 