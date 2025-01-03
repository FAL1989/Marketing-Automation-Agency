from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.monitoring import MonitoringMetric
from app.repositories.base import BaseRepository

class MonitoringRepository(BaseRepository):
    """
    Repositório para métricas de monitoramento
    """
    def __init__(
        self,
        session: AsyncSession
    ):
        super().__init__(
            session=session,
            model=MonitoringMetric
        )
        
    async def get_latest_metrics(
        self,
        metric_type: Optional[str] = None,
        limit: int = 100
    ) -> List[MonitoringMetric]:
        """
        Obtém métricas mais recentes
        """
        filters = {}
        if metric_type:
            filters["metric_type"] = metric_type
            
        return await self.get_by_filter(
            filters=filters,
            skip=0,
            limit=limit
        )
        
    async def get_metrics_by_timerange(
        self,
        start_time: float,
        end_time: float,
        metric_type: Optional[str] = None
    ) -> List[MonitoringMetric]:
        """
        Obtém métricas por intervalo de tempo
        """
        filters = {
            "timestamp__gte": start_time,
            "timestamp__lte": end_time
        }
        if metric_type:
            filters["metric_type"] = metric_type
            
        return await self.get_by_filter(filters=filters)
        
    async def get_metrics_summary(
        self,
        metric_type: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Obtém resumo das métricas
        """
        metrics = await self.get_latest_metrics(
            metric_type=metric_type,
            limit=1000
        )
        
        if not metrics:
            return {
                "min": 0.0,
                "max": 0.0,
                "avg": 0.0,
                "count": 0
            }
            
        values = [m.value for m in metrics]
        return {
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "count": len(values)
        }
        
    async def record_metric(
        self,
        metric_type: str,
        value: float,
        timestamp: Optional[float] = None,
        metadata: Optional[Dict] = None
    ) -> MonitoringMetric:
        """
        Registra nova métrica
        """
        metric = MonitoringMetric(
            metric_type=metric_type,
            value=value,
            timestamp=datetime.fromtimestamp(timestamp) if timestamp else None,
            metadata=metadata
        )
        
        self.session.add(metric)
        await self.session.commit()
        await self.session.refresh(metric)
        return metric 