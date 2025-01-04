from typing import Dict, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class SystemMetrics(BaseModel):
    """
    Modelo para métricas do sistema
    """
    model_config = ConfigDict(from_attributes=True)

    cpu: Dict
    memory: Dict
    swap: Dict
    disk: Dict
    network: Dict

class ApplicationMetrics(BaseModel):
    """
    Modelo para métricas da aplicação
    """
    model_config = ConfigDict(from_attributes=True)

    cpu: Dict
    memory: Dict
    threads: int
    open_files: int
    status: str

class MetricSummary(BaseModel):
    """
    Modelo para resumo de métricas
    """
    model_config = ConfigDict(from_attributes=True)

    min: float
    max: float
    avg: float
    count: int

class MetricRecord(BaseModel):
    """
    Modelo para registro de métrica
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    metric_type: str
    value: float
    timestamp: float
    metadata: Optional[Dict] = None

class MonitoringMetricCreate(BaseModel):
    """
    Schema para criação de métrica de monitoramento
    """
    model_config = ConfigDict(from_attributes=True)

    metric_type: str
    value: float
    timestamp: Optional[float] = None
    metadata: Optional[Dict] = None

class MonitoringMetricResponse(BaseModel):
    """
    Schema para resposta de métrica de monitoramento
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    metric_type: str
    value: float
    timestamp: float
    metadata: Optional[Dict] = None 