from typing import Dict, Optional
from pydantic import BaseModel
from datetime import datetime

class SystemMetrics(BaseModel):
    """
    Modelo para métricas do sistema
    """
    cpu: Dict
    memory: Dict
    swap: Dict
    disk: Dict
    network: Dict

    class Config:
        from_attributes = True

class ApplicationMetrics(BaseModel):
    """
    Modelo para métricas da aplicação
    """
    cpu: Dict
    memory: Dict
    threads: int
    open_files: int
    status: str

    class Config:
        from_attributes = True

class MetricSummary(BaseModel):
    """
    Modelo para resumo de métricas
    """
    min: float
    max: float
    avg: float
    count: int

    class Config:
        from_attributes = True

class MetricRecord(BaseModel):
    """
    Modelo para registro de métrica
    """
    id: str
    metric_type: str
    value: float
    timestamp: float
    metadata: Optional[Dict] = None

    class Config:
        from_attributes = True

class MonitoringMetricCreate(BaseModel):
    """
    Schema para criação de métrica de monitoramento
    """
    metric_type: str
    value: float
    timestamp: Optional[float] = None
    metadata: Optional[Dict] = None

    class Config:
        from_attributes = True

class MonitoringMetricResponse(BaseModel):
    """
    Schema para resposta de métrica de monitoramento
    """
    id: str
    metric_type: str
    value: float
    timestamp: float
    metadata: Optional[Dict] = None

    class Config:
        from_attributes = True 