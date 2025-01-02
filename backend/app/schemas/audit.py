from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime

class AuditLogBase(BaseModel):
    """Schema base para logs de auditoria"""
    event_type: str = Field(..., description="Tipo do evento")
    user_id: Optional[int] = Field(None, description="ID do usuário")
    ip_address: Optional[str] = Field(None, description="Endereço IP")
    severity: str = Field("info", description="Severidade do evento")
    details: Optional[Dict] = Field(None, description="Detalhes do evento")

class AuditLogCreate(AuditLogBase):
    """Schema para criação de logs"""
    pass

class AuditLogResponse(AuditLogBase):
    """Schema para resposta de logs"""
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

class AuditLogFilters(BaseModel):
    """Schema para filtros de busca"""
    start_date: Optional[datetime] = Field(None, description="Data inicial")
    end_date: Optional[datetime] = Field(None, description="Data final")
    event_types: Optional[List[str]] = Field(None, description="Tipos de evento")
    user_id: Optional[int] = Field(None, description="ID do usuário")
    ip_address: Optional[str] = Field(None, description="Endereço IP")
    severity: Optional[str] = Field(None, description="Severidade mínima")
    limit: int = Field(100, ge=1, le=1000, description="Limite de resultados")
    offset: int = Field(0, ge=0, description="Offset para paginação")

class EventTypeCount(BaseModel):
    """Schema para contagem de eventos por tipo"""
    event_type: str
    count: int

class SeverityCount(BaseModel):
    """Schema para contagem de eventos por severidade"""
    severity: str
    count: int

class IPCount(BaseModel):
    """Schema para contagem de eventos por IP"""
    ip_address: str
    count: int

class AuditLogStatistics(BaseModel):
    """Schema para estatísticas dos logs"""
    events_by_type: Dict[str, int] = Field(..., description="Eventos por tipo")
    events_by_severity: Dict[str, int] = Field(..., description="Eventos por severidade")
    top_ips: Dict[str, int] = Field(..., description="Top IPs com mais eventos")

class SecurityEventResponse(AuditLogResponse):
    """Schema para eventos de segurança"""
    severity: str = Field(..., description="Severidade do evento")
    details: Dict = Field(..., description="Detalhes do evento de segurança")

class AuditLogExportRequest(BaseModel):
    """Schema para requisição de exportação"""
    format: str = Field(..., pattern="^(csv|json)$", description="Formato de exportação")
    start_date: Optional[datetime] = Field(None, description="Data inicial")
    end_date: Optional[datetime] = Field(None, description="Data final")
    event_types: Optional[List[str]] = Field(None, description="Tipos de evento")

class UserActivityResponse(BaseModel):
    """Schema para atividade do usuário"""
    user_id: int
    logs: List[AuditLogResponse]
    summary: Dict[str, int] = Field(..., description="Resumo de atividades por tipo") 