from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import Request
from sqlalchemy.orm import Session
from ..models.audit import AuditLog
import json
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger("audit")
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

class AuditLogger:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def log_event(self, event_type: str, user_id: Optional[int] = None, 
                       details: Optional[Dict] = None, request: Optional[Request] = None, 
                       db: Optional[Session] = None) -> None:
        try:
            event_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "user_id": user_id,
                "details": details or {}
            }

            if request:
                event_data.update({
                    "ip_address": request.client.host,
                    "method": request.method,
                    "path": str(request.url.path),
                    "user_agent": request.headers.get("user-agent")
                })

            logger.info(event_type, extra=event_data)

            if db:
                db.add(AuditLog(**event_data))
                await db.commit()

        except Exception as e:
            logger.error(f"Erro ao registrar evento: {str(e)}")

    async def get_events(self, db: Session, **filters) -> List[AuditLog]:
        try:
            query = db.query(AuditLog)
            for field, value in filters.items():
                if value is not None:
                    query = query.filter(getattr(AuditLog, field) == value)
            return await query.order_by(AuditLog.timestamp.desc()).all()
        except Exception as e:
            logger.error(f"Erro ao recuperar eventos: {str(e)}")
            return []

    async def cleanup_old_events(self, db: Session, days: int = 90) -> int:
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            deleted = await db.query(AuditLog).filter(
                AuditLog.timestamp < cutoff
            ).delete()
            await db.commit()
            return deleted
        except Exception as e:
            logger.error(f"Erro ao limpar eventos: {str(e)}")
            return 0

    async def export_events(self, db: Session, start_date: datetime, 
                          end_date: datetime, format: str = "json") -> str:
        try:
            events = await self.get_events(db, start_date=start_date, end_date=end_date)
            if format == "json":
                return json.dumps([e.to_dict() for e in events])
            elif format == "csv":
                import csv, io
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=["timestamp", "event_type", "user_id", "details"])
                writer.writeheader()
                writer.writerows([e.to_dict() for e in events])
                return output.getvalue()
            raise ValueError(f"Formato não suportado: {format}")
        except Exception as e:
            logger.error(f"Erro ao exportar eventos: {str(e)}")
            return ""

audit_logger = AuditLogger() 