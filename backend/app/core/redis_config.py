from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
from .config import settings
from .optimizations import REDIS_OPTIMIZATIONS
import os

# Configuração de retry mais robusta e otimizada
REDIS_RETRY = Retry(
    ExponentialBackoff(cap=10, base=1.2),  # Backoff mais gradual e com cap maior
    retries=7,  # Aumentado número de tentativas
    supported_errors=(
        Exception,  # Captura qualquer erro
    )
)

# Configurações otimizadas do Redis
REDIS_CONFIG = {
    "url": "redis://localhost:6379/1" if os.getenv("TESTING", "").lower() == "true" else settings.REDIS_URL,
    "decode_responses": True,
    "socket_timeout": 3.0,  # Reduzido para maior responsividade
    "socket_connect_timeout": 3.0,  # Reduzido para maior responsividade
    "retry_on_timeout": True,
    "health_check_interval": 15,  # Reduzido para detecção mais rápida de problemas
    "max_connections": 150,  # Aumentado pool de conexões
    "retry": REDIS_RETRY,
    "encoding": "utf-8",
    "max_retries": 3,
    "retry_on_error": [Exception],  # Retry em qualquer erro
    "pool_timeout": 5,  # Timeout para obter conexão do pool
    "socket_keepalive": True,  # Mantém conexões ativas
    "socket_keepalive_options": {
        "tcp_keepidle": 60,  # Tempo antes do primeiro keepalive
        "tcp_keepintvl": 30,  # Intervalo entre keepalives
        "tcp_keepcnt": 3  # Número de keepalives antes de considerar conexão morta
    }
}

# Configurações adicionais do Redis para otimização
REDIS_RUNTIME_CONFIG = {
    # Configurações de memória
    "maxmemory": REDIS_OPTIMIZATIONS["max_memory"],
    "maxmemory-policy": REDIS_OPTIMIZATIONS["maxmemory_policy"],
    "maxmemory-samples": REDIS_OPTIMIZATIONS["maxmemory_samples"],
    
    # Configurações de desfragmentação
    "activedefrag": REDIS_OPTIMIZATIONS["active_defrag"],
    "active-defrag-threshold-lower": REDIS_OPTIMIZATIONS["active_defrag_threshold_lower"],
    "active-defrag-threshold-upper": REDIS_OPTIMIZATIONS["active_defrag_threshold_upper"],
    "active-defrag-cycle-min": REDIS_OPTIMIZATIONS["active_defrag_cycle_min"],
    "active-defrag-cycle-max": REDIS_OPTIMIZATIONS["active_defrag_cycle_max"],
    
    # Configurações de LFU (Least Frequently Used)
    "lfu-decay-time": REDIS_OPTIMIZATIONS["lfu_decay_time"],
    "lfu-log-factor": REDIS_OPTIMIZATIONS["lfu_log_factor"],
    
    # Outras otimizações
    "lazyfree-lazy-eviction": "yes",  # Evicção assíncrona
    "lazyfree-lazy-expire": "yes",  # Expiração assíncrona
    "lazyfree-lazy-server-del": "yes",  # Deleção assíncrona
    "replica-lazy-flush": "yes",  # Flush assíncrono
    "dynamic-hz": "yes",  # Ajuste dinâmico do Hz
    "maxclients": 10000,  # Limite de clientes aumentado
    "timeout": 0,  # Desativa timeout de conexão
    "tcp-keepalive": 300,  # Keepalive TCP
    "appendonly": "yes",  # Habilita persistência
    "appendfsync": "everysec",  # Sync a cada segundo
    "no-appendfsync-on-rewrite": "yes",  # Evita sync durante rewrite
    "auto-aof-rewrite-percentage": 100,  # Rewrite quando dobrar de tamanho
    "auto-aof-rewrite-min-size": "64mb",  # Tamanho mínimo para rewrite
    "aof-use-rdb-preamble": "yes",  # Usa RDB no início do AOF
    "aof-timestamp-enabled": "yes",  # Adiciona timestamps no AOF
    
    # Otimizações de rede
    "tcp-backlog": 511,  # Aumenta backlog TCP
    "tcp-keepalive": 300,  # Keepalive TCP
    "repl-timeout": 60,  # Timeout de replicação
    "repl-ping-replica-period": 10,  # Ping mais frequente
    "repl-backlog-size": "100mb",  # Buffer de replicação maior
    
    # Otimizações de CPU
    "io-threads": 4,  # Threads de I/O
    "io-threads-do-reads": "yes",  # Usa threads para leitura
    "hz": 50,  # Aumenta frequência de tarefas em background
    
    # Otimizações de memória
    "activerehashing": "yes",  # Rehashing ativo
    "hash-max-ziplist-entries": 512,  # Otimiza estruturas pequenas
    "hash-max-ziplist-value": 64,  # Otimiza estruturas pequenas
    "list-max-ziplist-size": -2,  # Otimiza listas
    "list-compress-depth": 0,  # Desativa compressão de listas
    "set-max-intset-entries": 512,  # Otimiza sets pequenos
    "zset-max-ziplist-entries": 128,  # Otimiza zsets pequenos
    "zset-max-ziplist-value": 64,  # Otimiza zsets pequenos
    "stream-node-max-bytes": "4kb",  # Otimiza streams
    "stream-node-max-entries": 100  # Otimiza streams
}

async def configure_redis(redis_client):
    """
    Aplica configurações otimizadas no servidor Redis.
    Deve ser chamado durante a inicialização da aplicação.
    """
    try:
        # Aplica configurações
        for key, value in REDIS_RUNTIME_CONFIG.items():
            await redis_client.config_set(key, value)
            
        # Verifica configurações aplicadas
        config = await redis_client.config_get('*')
        
        # Logs de configuração
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Configurações do Redis aplicadas com sucesso")
        logger.debug(f"Configuração atual do Redis: {config}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao configurar Redis: {str(e)}")
        return False 