import logging
import psutil
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.monitoring_repository import MonitoringRepository

logger = logging.getLogger(__name__)

class MonitoringService:
    """
    Serviço para monitoramento do sistema e aplicação
    """
    def __init__(
        self,
        session: AsyncSession
    ):
        self.repository = MonitoringRepository(
            session=session
        )
        
    async def get_system_metrics(self) -> Dict:
        """
        Obtém métricas do sistema
        """
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memória
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disco
            disk = psutil.disk_usage("/")
            
            # Rede
            net = psutil.net_io_counters()
            
            metrics = {
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "freq_current": cpu_freq.current if cpu_freq else 0,
                    "freq_min": cpu_freq.min if cpu_freq else 0,
                    "freq_max": cpu_freq.max if cpu_freq else 0
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                    "free": memory.free
                },
                "swap": {
                    "total": swap.total,
                    "used": swap.used,
                    "free": swap.free,
                    "percent": swap.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent
                },
                "network": {
                    "bytes_sent": net.bytes_sent,
                    "bytes_recv": net.bytes_recv,
                    "packets_sent": net.packets_sent,
                    "packets_recv": net.packets_recv,
                    "errin": net.errin,
                    "errout": net.errout,
                    "dropin": net.dropin,
                    "dropout": net.dropout
                }
            }
            
            # Registra métricas
            timestamp = datetime.utcnow().timestamp()
            
            await self.repository.record_metric(
                metric_type="cpu_percent",
                value=cpu_percent,
                timestamp=timestamp,
                metadata=metrics["cpu"]
            )
            
            await self.repository.record_metric(
                metric_type="memory_percent",
                value=memory.percent,
                timestamp=timestamp,
                metadata=metrics["memory"]
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Erro ao obter métricas do sistema: {str(e)}")
            raise
            
    async def get_application_metrics(self) -> Dict:
        """
        Obtém métricas da aplicação
        """
        try:
            # Processo atual
            process = psutil.Process()
            
            # CPU
            cpu_percent = process.cpu_percent(interval=1)
            cpu_times = process.cpu_times()
            
            # Memória
            memory = process.memory_info()
            
            # Threads e arquivos
            threads = process.num_threads()
            files = len(process.open_files())
            
            metrics = {
                "cpu": {
                    "percent": cpu_percent,
                    "user": cpu_times.user,
                    "system": cpu_times.system,
                    "children_user": cpu_times.children_user,
                    "children_system": cpu_times.children_system
                },
                "memory": {
                    "rss": memory.rss,
                    "vms": memory.vms,
                    "shared": memory.shared,
                    "text": memory.text,
                    "lib": memory.lib,
                    "data": memory.data,
                    "dirty": memory.dirty
                },
                "threads": threads,
                "open_files": files,
                "status": process.status()
            }
            
            # Registra métricas
            timestamp = datetime.utcnow().timestamp()
            
            await self.repository.record_metric(
                metric_type="app_cpu_percent",
                value=cpu_percent,
                timestamp=timestamp,
                metadata=metrics["cpu"]
            )
            
            await self.repository.record_metric(
                metric_type="app_memory_rss",
                value=memory.rss,
                timestamp=timestamp,
                metadata=metrics["memory"]
            )
            
            await self.repository.record_metric(
                metric_type="app_threads",
                value=threads,
                timestamp=timestamp
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Erro ao obter métricas da aplicação: {str(e)}")
            return {}
            
    async def get_metrics_history(
        self,
        metric_type: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> List[Dict]:
        """
        Obtém histórico de métricas
        """
        try:
            metrics = await self.repository.get_metrics_by_timerange(
                start_time=start_time,
                end_time=end_time,
                metric_type=metric_type
            )
            return [m.to_dict() for m in metrics]
            
        except Exception as e:
            logger.error(f"Erro ao obter histórico de métricas: {str(e)}")
            return []
            
    async def get_metrics_summary(
        self,
        metric_type: Optional[str] = None
    ) -> Dict:
        """
        Obtém resumo das métricas
        """
        try:
            return await self.repository.get_metrics_summary(
                metric_type=metric_type
            )
            
        except Exception as e:
            logger.error(f"Erro ao obter resumo de métricas: {str(e)}")
            return {
                "min": 0.0,
                "max": 0.0,
                "avg": 0.0,
                "count": 0
            }
            
    async def cleanup_metrics(
        self,
        older_than: Optional[float] = None
    ) -> int:
        """
        Remove métricas antigas
        """
        try:
            if older_than is None:
                # Remove métricas mais antigas que 30 dias
                older_than = (
                    datetime.utcnow().timestamp() - (30 * 24 * 60 * 60)
                )
                
            return await self.repository.cleanup_old_metrics(
                older_than=older_than
            )
            
        except Exception as e:
            logger.error(f"Erro ao limpar métricas antigas: {str(e)}")
            return 0 