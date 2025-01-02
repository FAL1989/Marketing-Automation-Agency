from typing import Any, Dict, Optional, Callable, Awaitable
import json
import asyncio
import logging
from datetime import datetime, timedelta
from ..core.redis import redis_manager
from .monitoring_service import MonitoringService

logger = logging.getLogger(__name__)

class QueueService:
    def __init__(
        self,
        redis_url: str,
        monitoring_service: MonitoringService
    ):
        """
        Inicializa o serviço de filas.
        
        Args:
            redis_url: URL de conexão com o Redis (mantido para compatibilidade)
            monitoring_service: Serviço de monitoramento para métricas
        """
        self.monitoring = monitoring_service
        self.processing_tasks: Dict[str, asyncio.Task] = {}
        
    async def _get_redis(self):
        """Obtém cliente Redis do gerenciador central"""
        return await redis_manager.get_client('queue')

    async def enqueue(
        self,
        queue_name: str,
        data: Dict[str, Any],
        priority: int = 0,
        delay: Optional[int] = None
    ) -> str:
        """Adiciona um item à fila"""
        try:
            item_id = f"{queue_name}:{datetime.utcnow().timestamp()}"
            score = priority * 1000 + (datetime.utcnow().timestamp() if not delay else datetime.utcnow().timestamp() + delay)
            
            async with await self._get_redis() as redis:
                # Adiciona à fila principal ou de delay
                target_queue = f"{queue_name}:delayed" if delay else queue_name
                await redis.zadd(
                    target_queue,
                    {json.dumps({"id": item_id, "data": data}): score}
                )
                
            return item_id
        except Exception as e:
            logger.error(f"Erro ao enfileirar item: {str(e)}")
            raise

    async def start_worker(
        self,
        queue_name: str,
        handler: Callable[[Dict[str, Any]], Awaitable[Any]],
        batch_size: int = 1,
        polling_interval: float = 1.0
    ) -> None:
        """Inicia um worker para processar itens da fila"""
        if queue_name in self.processing_tasks:
            return

        async def process_queue():
            while True:
                try:
                    async with await self._get_redis() as redis:
                        # Move itens atrasados para a fila principal
                        now = datetime.utcnow().timestamp()
                        delayed_items = await redis.zrangebyscore(
                            f"{queue_name}:delayed",
                            0,
                            now,
                            withscores=True
                        )
                        
                        if delayed_items:
                            await redis.zremrangebyscore(
                                f"{queue_name}:delayed",
                                0,
                                now
                            )
                            for item, score in delayed_items:
                                await redis.zadd(queue_name, {item: score})
                        
                        # Processa itens da fila principal
                        items = await redis.zrange(
                            queue_name,
                            0,
                            batch_size - 1,
                            withscores=True
                        )
                        
                        if not items:
                            await asyncio.sleep(polling_interval)
                            continue
                        
                        for item_json, _ in items:
                            item = json.loads(item_json)
                            try:
                                await handler(item["data"])
                                await redis.zrem(queue_name, item_json)
                            except Exception as e:
                                logger.error(f"Erro ao processar item {item['id']}: {str(e)}")
                                # Move para fila de erro
                                await redis.zadd(
                                    f"{queue_name}:errors",
                                    {item_json: datetime.utcnow().timestamp()}
                                )
                                await redis.zrem(queue_name, item_json)
                                
                except Exception as e:
                    logger.error(f"Erro no worker da fila {queue_name}: {str(e)}")
                    await asyncio.sleep(polling_interval)

        self.processing_tasks[queue_name] = asyncio.create_task(process_queue())

    async def stop_worker(self, queue_name: str) -> None:
        """Para um worker específico"""
        if queue_name in self.processing_tasks:
            self.processing_tasks[queue_name].cancel()
            try:
                await self.processing_tasks[queue_name]
            except asyncio.CancelledError:
                pass
            del self.processing_tasks[queue_name]

    async def get_queue_size(self, queue_name: str) -> int:
        """Retorna o número de itens na fila"""
        try:
            async with await self._get_redis() as redis:
                return await redis.zcard(queue_name)
        except Exception as e:
            logger.error(f"Erro ao obter tamanho da fila: {str(e)}")
            return 0

    async def clear_queue(self, queue_name: str) -> None:
        """Limpa todos os itens de uma fila"""
        try:
            async with await self._get_redis() as redis:
                await redis.delete(queue_name)
                await redis.delete(f"{queue_name}:delayed")
        except Exception as e:
            logger.error(f"Erro ao limpar fila: {str(e)}")
            raise

    async def close(self) -> None:
        """Para todos os workers"""
        for queue_name in list(self.processing_tasks.keys()):
            await self.stop_worker(queue_name) 