"""
Módulo para integração com ClickHouse para métricas.
"""

from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)

class ClickHouseClient:
    """Cliente para interação com o ClickHouse"""
    
    def __init__(self):
        self.enabled = False  # Desabilitado por padrão
        
    async def connect(self):
        """Conecta ao ClickHouse"""
        pass
    
    async def store_metric(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """Armazena uma métrica"""
        if not self.enabled:
            return
        
    async def get_metrics(self, metric_name: str, start_time: datetime, end_time: datetime = None) -> List[Dict[str, Any]]:
        """Recupera métricas"""
        if not self.enabled:
            return []
        return []

clickhouse_client = ClickHouseClient()

async def get_metrics(metric_name: str, hours: int = 24) -> List[Dict[str, Any]]:
    """Helper function para obter métricas"""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    return await clickhouse_client.get_metrics(metric_name, start_time, end_time) 