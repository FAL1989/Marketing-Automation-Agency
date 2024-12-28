from typing import Any, Dict, Optional, Callable, Awaitable
import json
import asyncio
from redis import asyncio as aioredis
import logging
from datetime import datetime, timedelta
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
            redis_url: URL de conexão com o Redis
            monitoring_service: Serviço de monitoramento para métricas
        """
        self.redis = aioredis.from_url(redis_url)
        self.monitoring = monitoring_service
        self.processing_tasks: Dict[str, asyncio.Task] = {}
    
    async def enqueue(
        self,
        queue_name: str,
        data: Dict[str, Any],
        priority: int = 0,
        delay: Optional[int] = None
    ) -> str:
        """
        Adiciona um item à fila.
        
        Args:
            queue_name: Nome da fila
            data: Dados a serem enfileirados
            priority: Prioridade (0-9, maior = mais prioritário)
            delay: Atraso em segundos antes do processamento
            
        Returns:
            str: ID do item na fila
        """
        try:
            # Gera um ID único para o item
            item_id = f"{queue_name}:{datetime.utcnow().timestamp()}:{priority}"
            
            # Prepara o item
            item = {
                "id": item_id,
                "data": data,
                "priority": priority,
                "created_at": datetime.utcnow().isoformat(),
                "status": "pending"
            }
            
            # Se houver delay, adiciona à fila atrasada
            if delay:
                process_at = datetime.utcnow() + timedelta(seconds=delay)
                await self.redis.zadd(
                    f"{queue_name}:delayed",
                    {json.dumps(item): process_at.timestamp()}
                )
            else:
                # Adiciona à fila principal com prioridade
                await self.redis.zadd(
                    queue_name,
                    {json.dumps(item): -priority}
                )
            
            # Registra métrica de item enfileirado
            self.monitoring.increment_counter(
                "queue_items_total",
                {"queue": queue_name, "status": "enqueued"}
            )
            
            return item_id
            
        except Exception as e:
            logger.error(f"Erro ao enfileirar item: {str(e)}")
            raise
    
    async def dequeue(
        self,
        queue_name: str,
        timeout: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Remove e retorna o próximo item da fila.
        
        Args:
            queue_name: Nome da fila
            timeout: Tempo máximo de espera em segundos
            
        Returns:
            Dict | None: Item da fila ou None se vazia
        """
        try:
            # Primeiro, move itens atrasados que já podem ser processados
            await self._process_delayed_items(queue_name)
            
            # Tenta obter o próximo item
            result = await self.redis.zpopmin(queue_name)
            
            if not result:
                if timeout > 0:
                    # Espera por novos itens
                    await asyncio.sleep(timeout)
                    return await self.dequeue(queue_name, 0)
                return None
            
            # Decodifica o item
            item = json.loads(result[0][0])
            
            # Registra métrica de item processado
            self.monitoring.increment_counter(
                "queue_items_total",
                {"queue": queue_name, "status": "dequeued"}
            )
            
            return item
            
        except Exception as e:
            logger.error(f"Erro ao desenfileirar item: {str(e)}")
            raise
    
    async def _process_delayed_items(self, queue_name: str) -> None:
        """Processa itens atrasados que já podem ser executados"""
        try:
            now = datetime.utcnow().timestamp()
            
            # Obtém itens que já podem ser processados
            items = await self.redis.zrangebyscore(
                f"{queue_name}:delayed",
                0,
                now,
                withscores=True
            )
            
            if not items:
                return
            
            # Move cada item para a fila principal
            for item_json, _ in items:
                item = json.loads(item_json)
                await self.redis.zadd(
                    queue_name,
                    {item_json: -item["priority"]}
                )
                await self.redis.zrem(f"{queue_name}:delayed", item_json)
                
        except Exception as e:
            logger.error(f"Erro ao processar itens atrasados: {str(e)}")
    
    async def start_worker(
        self,
        queue_name: str,
        handler: Callable[[Dict[str, Any]], Awaitable[None]],
        batch_size: int = 1,
        polling_interval: int = 1
    ) -> None:
        """
        Inicia um worker para processar itens da fila.
        
        Args:
            queue_name: Nome da fila
            handler: Função assíncrona para processar os itens
            batch_size: Número de itens a processar por vez
            polling_interval: Intervalo entre verificações da fila
        """
        async def worker():
            while True:
                try:
                    items = []
                    for _ in range(batch_size):
                        item = await self.dequeue(queue_name)
                        if item:
                            items.append(item)
                        if len(items) < batch_size:
                            break
                    
                    if items:
                        # Processa os itens em batch
                        for item in items:
                            try:
                                await handler(item["data"])
                                self.monitoring.increment_counter(
                                    "queue_items_total",
                                    {"queue": queue_name, "status": "processed"}
                                )
                            except Exception as e:
                                logger.error(
                                    f"Erro ao processar item {item['id']}: {str(e)}"
                                )
                                self.monitoring.increment_counter(
                                    "queue_items_total",
                                    {"queue": queue_name, "status": "failed"}
                                )
                    else:
                        # Aguarda antes da próxima verificação
                        await asyncio.sleep(polling_interval)
                        
                except Exception as e:
                    logger.error(f"Erro no worker da fila {queue_name}: {str(e)}")
                    await asyncio.sleep(polling_interval)
        
        # Inicia o worker como uma task
        task = asyncio.create_task(worker())
        self.processing_tasks[queue_name] = task
    
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
            return await self.redis.zcard(queue_name)
        except Exception as e:
            logger.error(f"Erro ao obter tamanho da fila: {str(e)}")
            return 0
    
    async def clear_queue(self, queue_name: str) -> None:
        """Limpa todos os itens de uma fila"""
        try:
            await self.redis.delete(queue_name)
            await self.redis.delete(f"{queue_name}:delayed")
        except Exception as e:
            logger.error(f"Erro ao limpar fila: {str(e)}")
            raise
    
    async def close(self) -> None:
        """Fecha a conexão com o Redis e para todos os workers"""
        # Para todos os workers
        for queue_name in list(self.processing_tasks.keys()):
            await self.stop_worker(queue_name)
        
        # Fecha conexão com Redis
        await self.redis.close() 