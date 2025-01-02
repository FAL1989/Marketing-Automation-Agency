from redis.asyncio import Redis, ConnectionPool
from typing import Dict, Optional
import logging
import asyncio
from .config import settings

logger = logging.getLogger(__name__)

class RedisManager:
    """
    Gerenciador de conexões Redis com suporte a múltiplos bancos
    """
    def __init__(self):
        self._pools: Dict[str, ConnectionPool] = {}
        self._connections: Dict[str, Redis] = {}
        self._lock = asyncio.Lock()
        self._initialized = False
        
        # Configurações padrão
        self.default_pool_size = 10
        self.default_socket_timeout = 5.0
        self.default_socket_connect_timeout = 5.0
        
        # Mapeamento de nomes para números de banco
        self.db_map = {
            'default': settings.REDIS_DB,
            'rate_limit': settings.REDIS_RATELIMIT_DB
        }
    
    async def initialize(self) -> None:
        """
        Inicializa as pools de conexão
        """
        async with self._lock:
            if self._initialized:
                return
            
            try:
                # Cria pools para cada banco
                for name, db in self.db_map.items():
                    pool = ConnectionPool(
                        host=settings.REDIS_HOST,
                        port=settings.REDIS_PORT,
                        db=db,
                        max_connections=self.default_pool_size,
                        socket_timeout=self.default_socket_timeout,
                        socket_connect_timeout=self.default_socket_connect_timeout,
                        decode_responses=True,
                        retry_on_timeout=True
                    )
                    self._pools[name] = pool
                    logger.info(f"Pool Redis criada para {name} (db={db})")
                
                self._initialized = True
                logger.info("RedisManager inicializado com sucesso")
                
            except Exception as e:
                logger.error(f"Erro ao inicializar RedisManager: {e}")
                raise
    
    async def get_connection(self, name: str = 'default') -> Redis:
        """
        Obtém uma conexão do pool especificado
        """
        if not self._initialized:
            await self.initialize()
        
        if name not in self._pools:
            raise ValueError(f"Pool '{name}' não encontrada")
        
        try:
            # Cria uma nova conexão se não existir
            if name not in self._connections:
                self._connections[name] = Redis(
                    connection_pool=self._pools[name],
                    decode_responses=True
                )
            
            return self._connections[name]
            
        except Exception as e:
            logger.error(f"Erro ao obter conexão Redis para {name}: {e}")
            raise
    
    async def close(self, name: Optional[str] = None) -> None:
        """
        Fecha conexões e pools
        """
        async with self._lock:
            try:
                if name:
                    # Fecha apenas a conexão e pool especificadas
                    if name in self._connections:
                        await self._connections[name].aclose()
                        del self._connections[name]
                    if name in self._pools:
                        await self._pools[name].disconnect(inuse_connections=True)
                        del self._pools[name]
                    logger.info(f"Conexão Redis fechada para {name}")
                else:
                    # Fecha todas as conexões e pools
                    for conn in self._connections.values():
                        await conn.aclose()
                    for pool in self._pools.values():
                        await pool.disconnect(inuse_connections=True)
                    self._connections.clear()
                    self._pools.clear()
                    self._initialized = False
                    logger.info("Todas as conexões Redis fechadas")
                    
            except Exception as e:
                logger.error(f"Erro ao fechar conexões Redis: {e}")
                raise
    
    async def ping(self, name: str = 'default') -> bool:
        """
        Verifica se a conexão está ativa
        """
        try:
            conn = await self.get_connection(name)
            return await conn.ping()
        except Exception as e:
            logger.error(f"Erro ao verificar conexão Redis para {name}: {e}")
            return False
    
    async def flushdb(self, name: str = 'default') -> None:
        """
        Limpa o banco de dados especificado
        """
        try:
            conn = await self.get_connection(name)
            await conn.flushdb()
            logger.info(f"Banco Redis {name} limpo")
        except Exception as e:
            logger.error(f"Erro ao limpar banco Redis {name}: {e}")
            raise
    
    async def __aenter__(self):
        """Suporte para context manager assíncrono"""
        if not self._initialized:
            await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup ao sair do context manager"""
        await self.close()

redis_manager = RedisManager() 