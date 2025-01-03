from datetime import datetime
import uuid
from typing import Dict, Optional
from sqlalchemy import Column, Float, String, JSON, DateTime
from app.db.base_all import Base

class MonitoringMetric(Base):
    """
    Modelo para métricas de monitoramento
    """
    __tablename__ = "monitoring_metrics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    metric_type = Column(String, nullable=False, index=True)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    metric_metadata = Column(JSON, nullable=True)
    
    def __init__(
        self,
        metric_type: str,
        value: float,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Inicializa uma nova métrica
        """
        self.id = str(uuid.uuid4())
        self.metric_type = metric_type
        self.value = value
        self.timestamp = timestamp or datetime.utcnow()
        self.metric_metadata = metadata or {}
        
    def to_dict(self) -> Dict:
        """
        Converte para dicionário
        """
        return {
            "id": self.id,
            "metric_type": self.metric_type,
            "value": self.value,
            "timestamp": self.timestamp.timestamp(),
            "metadata": self.metric_metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict) -> "MonitoringMetric":
        """
        Cria instância a partir de dicionário
        """
        timestamp = data.get("timestamp")
        if isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp)
            
        return cls(
            metric_type=data["metric_type"],
            value=data["value"],
            timestamp=timestamp,
            metadata=data.get("metadata")
        ) 