from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json
import csv
from io import StringIO
from fastapi import Request
from sqlalchemy import and_
from sqlalchemy.orm import Session
from ..models.audit import AuditLog
from ..models.user import User
from .config import settings
import logging
import structlog
from .events import EventType
import os

# Configuração do logger tradicional
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

# Configuração do logger estruturado
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

class AuditLogger:
    """Sistema de logging para auditoria de segurança"""
    
    def __init__(self):
        # Garante que o diretório de logs existe
        os.makedirs(settings.AUDIT_LOG_PATH, exist_ok=True)
        
        # Configura o logger tradicional
        self.traditional_logger = logging.getLogger("security.audit")
        self.file_handler = logging.FileHandler(f"{settings.AUDIT_LOG_PATH}/security_audit.log")
        self.file_handler.setFormatter(logging.Formatter('%(message)s'))
        self.traditional_logger.addHandler(self.file_handler)
        
        # Configura o logger estruturado
        self.logger = structlog.get_logger("security.audit")
    
    async def log_event(
        self,
        db: Session,
        event_type: EventType,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "info"
    ) -> None:
        """
        Registra um evento de auditoria
        
        Args:
            db: Sessão do banco de dados
            event_type: Tipo do evento
            user_id: ID do usuário (se autenticado)
            ip_address: Endereço IP
            details: Detalhes adicionais do evento
            severity: Severidade do evento (info, warning, error, critical)
        """
        timestamp = datetime.utcnow()
        
        # Cria o log estruturado
        log_data = {
            "timestamp": timestamp.isoformat(),
            "event_type": event_type.value,
            "user_id": user_id,
            "ip_address": ip_address,
            "severity": severity,
            "details": details or {}
        }
        
        # Registra no logger estruturado
        self.logger.info(
            event_type.value,
            **log_data
        )
        
        # Persiste no banco de dados
        audit_log = AuditLog(
            timestamp=timestamp,
            event_type=event_type.value,
            user_id=user_id,
            ip_address=ip_address,
            severity=severity,
            details=json.dumps(details) if details else None
        )
        
        db.add(audit_log)
        await db.flush()
    
    async def log_security_event(
        self,
        db: Session,
        event_type: EventType,
        request_info: Dict[str, Any],
        user_id: Optional[int] = None,
        severity: str = "warning"
    ) -> None:
        """
        Registra um evento de segurança
        
        Args:
            db: Sessão do banco de dados
            event_type: Tipo do evento
            request_info: Informações da requisição
            user_id: ID do usuário (se autenticado)
            severity: Severidade do evento
        """
        await self.log_event(
            db=db,
            event_type=event_type,
            user_id=user_id,
            ip_address=request_info.get("ip"),
            details={
                "path": request_info.get("path"),
                "method": request_info.get("method"),
                "user_agent": request_info.get("user_agent"),
                "headers": request_info.get("headers", {}),
                "query_params": request_info.get("query_params", {}),
                "body": request_info.get("body", {})
            },
            severity=severity
        )
    
    async def log_auth_event(
        self,
        db: Session,
        event_type: EventType,
        user_id: int,
        ip_address: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Registra um evento de autenticação
        
        Args:
            db: Sessão do banco de dados
            event_type: Tipo do evento
            user_id: ID do usuário
            ip_address: Endereço IP
            success: Se a autenticação foi bem sucedida
            details: Detalhes adicionais
        """
        severity = "info" if success else "warning"
        await self.log_event(
            db=db,
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            details={
                "success": success,
                **(details or {})
            },
            severity=severity
        )

    async def get_events(
        self,
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_type: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> List[AuditLog]:
        """
        Consulta eventos de auditoria com filtros
        """
        query = db.query(AuditLog)
        
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
        if event_type:
            query = query.filter(AuditLog.event_type.like(f"{event_type}%"))
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
            
        return query.all()

    async def cleanup_old_events(self, db: Session, days: int = 90):
        """
        Remove eventos mais antigos que o número de dias especificado
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        db.query(AuditLog).filter(AuditLog.created_at < cutoff_date).delete()
        db.commit()

    async def export_events(
        self,
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = "json"
    ) -> str:
        """
        Exporta eventos de auditoria em diferentes formatos
        """
        events = await self.get_events(db, start_date, end_date)
        
        if format == "json":
            return json.dumps([{
                "id": e.id,
                "user_id": e.user_id,
                "event_type": e.event_type,
                "event_data": e.event_data,
                "ip_address": e.ip_address,
                "user_agent": e.user_agent,
                "created_at": e.created_at.isoformat()
            } for e in events], default=str)
            
        elif format == "csv":
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "id", "user_id", "event_type", "event_data",
                "ip_address", "user_agent", "created_at"
            ])
            for e in events:
                writer.writerow([
                    e.id, e.user_id, e.event_type, json.dumps(e.event_data),
                    e.ip_address, e.user_agent, e.created_at.isoformat()
                ])
            return output.getvalue()
            
        else:
            raise ValueError(f"Formato de exportação inválido: {format}")

# Instância global do logger de auditoria
audit_logger = AuditLogger() 