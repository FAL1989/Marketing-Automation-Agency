from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from ..database.connection import Base

class AuditLog(Base):
    """Modelo para logs de auditoria"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 tem 45 caracteres
    user_agent = Column(String(255), nullable=True)
    path = Column(String(255), nullable=True)
    method = Column(String(10), nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relacionamentos
    user = relationship("User", back_populates="audit_logs")

    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "user_id": self.user_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "path": self.path,
            "method": self.method,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        } 