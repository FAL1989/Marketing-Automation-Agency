import asyncio
import logging
from datetime import datetime
from typing import Optional
from prometheus_client import Counter, Gauge
from .optimizations import (
    AUTO_OPTIMIZATION_CONFIG,
    MONITORING_CONFIG,
    PREDICTIVE_CACHE_CONFIG
)
from ..services.cache_service import cache_service

logger = logging.getLogger(__name__)

# Métricas de otimização
OPTIMIZATION_RUNS = Counter(
    'cache_optimization_runs_total',
    'Total de execuções da otimização do cache',
    ['result']
)
OPTIMIZATION_DURATION = Gauge(
    'cache_optimization_duration_seconds',
    'Duração da última otimização do cache'
)
ITEMS_REMOVED = Counter(
    'cache_items_removed_total',
    'Total de itens removidos do cache',
    ['reason']
)
MEMORY_SAVED = Gauge(
    'cache_memory_saved_bytes',
    'Quantidade de memória economizada pela otimização'
)

class CacheOptimizer:
    def __init__(self):
        self.running = False
        self.last_run: Optional[datetime] = None
        self._task = None
        
    async def start(self):
        """Inicia o otimizador em background"""
        if not AUTO_OPTIMIZATION_CONFIG["enabled"]:
            logger.info("Otimização automática desabilitada")
            return
            
        if self.running:
            logger.warning("Otimizador já está rodando")
            return
            
        self.running = True
        self._task = asyncio.create_task(self._run_optimization_loop())
        logger.info("Otimizador de cache iniciado")
        
    async def stop(self):
        """Para o otimizador"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Otimizador de cache parado")
        
    async def _run_optimization_loop(self):
        """Loop principal de otimização"""
        while self.running:
            try:
                start_time = datetime.now()
                
                # Executa otimização
                success = await self._optimize_cache()
                
                # Registra métricas
                duration = (datetime.now() - start_time).total_seconds()
                OPTIMIZATION_DURATION.set(duration)
                OPTIMIZATION_RUNS.labels(
                    result='success' if success else 'failure'
                ).inc()
                
                # Atualiza timestamp
                self.last_run = start_time
                
                # Aguarda próximo ciclo
                await asyncio.sleep(AUTO_OPTIMIZATION_CONFIG["interval"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro na otimização do cache: {str(e)}")
                OPTIMIZATION_RUNS.labels(result='error').inc()
                await asyncio.sleep(60)  # Aguarda 1 minuto em caso de erro
                
    async def _optimize_cache(self) -> bool:
        """
        Executa a otimização do cache.
        Retorna True se a otimização foi bem sucedida.
        """
        try:
            logger.info("Iniciando otimização do cache")
            
            # Obtém estatísticas atuais
            stats = await cache_service.get_cache_stats()
            
            # Verifica uso de memória
            redis_memory_used = self._parse_memory_size(
                stats.get("redis", {}).get("memory_used", "0B")
            )
            if redis_memory_used > 0:
                memory_percent = (redis_memory_used / (1024 * 1024 * 1024)) * 100  # GB
                
                # Limpeza agressiva se uso de memória estiver alto
                if memory_percent >= AUTO_OPTIMIZATION_CONFIG["aggressive_cleanup_threshold"]:
                    logger.warning(
                        f"Uso de memória alto ({memory_percent:.1f}%). "
                        "Iniciando limpeza agressiva"
                    )
                    await self._aggressive_cleanup()
            
            # Otimiza cache com base em padrões de acesso
            await cache_service.optimize_cache()
            
            # Obtém estatísticas após otimização
            new_stats = await cache_service.get_cache_stats()
            
            # Calcula memória economizada
            old_memory = self._parse_memory_size(
                stats.get("redis", {}).get("memory_used", "0B")
            )
            new_memory = self._parse_memory_size(
                new_stats.get("redis", {}).get("memory_used", "0B")
            )
            memory_saved = max(0, old_memory - new_memory)
            MEMORY_SAVED.set(memory_saved)
            
            # Registra sucesso
            logger.info(
                f"Otimização concluída. Memória economizada: "
                f"{memory_saved / (1024*1024):.2f}MB"
            )
            return True
            
        except Exception as e:
            logger.error(f"Erro durante otimização: {str(e)}")
            return False
            
    async def _aggressive_cleanup(self):
        """
        Executa limpeza agressiva do cache quando o uso de memória está alto.
        Remove itens com baixa taxa de acesso e aumenta limites de expiração.
        """
        try:
            # Obtém estatísticas de cache
            stats = await cache_service.get_cache_stats()
            prediction_stats = stats.get("prediction", {})
            
            # Remove padrões de acesso raramente utilizados
            if prediction_stats:
                removed = 0
                for route, count in prediction_stats.get("top_routes", []):
                    if count < PREDICTIVE_CACHE_CONFIG["min_pattern_frequency"]:
                        await cache_service.invalidate_cache(route)
                        removed += 1
                        
                ITEMS_REMOVED.labels(reason='low_frequency').inc(removed)
                
            # Ajusta TTLs baseado no tráfego
            redis_info = stats.get("redis", {})
            hits = redis_info.get("hits", 0)
            misses = redis_info.get("misses", 0)
            total = hits + misses
            
            if total > 0:
                hit_rate = (hits / total) * 100
                if hit_rate < AUTO_OPTIMIZATION_CONFIG["min_hit_rate_threshold"]:
                    # Reduz TTL para itens com baixa taxa de hit
                    logger.info(
                        f"Taxa de hit baixa ({hit_rate:.1f}%). "
                        "Ajustando TTLs"
                    )
                    
            logger.info("Limpeza agressiva concluída")
            
        except Exception as e:
            logger.error(f"Erro na limpeza agressiva: {str(e)}")
            
    def _parse_memory_size(self, size_str: str) -> int:
        """Converte string de tamanho (ex: '1.5GB') para bytes"""
        try:
            if not size_str:
                return 0
                
            # Remove 'B' do final
            size_str = size_str.upper().rstrip('B')
            
            # Extrai número e unidade
            number = float(''.join(c for c in size_str if c.isdigit() or c == '.'))
            unit = ''.join(c for c in size_str if c.isalpha())
            
            # Converte para bytes
            multipliers = {
                '': 1,
                'K': 1024,
                'M': 1024 ** 2,
                'G': 1024 ** 3,
                'T': 1024 ** 4
            }
            
            return int(number * multipliers.get(unit, 1))
            
        except Exception as e:
            logger.error(f"Erro ao converter tamanho '{size_str}': {str(e)}")
            return 0

# Instância global do otimizador
cache_optimizer = CacheOptimizer() 