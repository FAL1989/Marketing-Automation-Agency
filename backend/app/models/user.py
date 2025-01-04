"""
Modelo de usuário do sistema
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..db.base_class import Base

class User(Base):
    """Modelo de usuário"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Campos de segurança
    failed_login_attempts = Column(Integer, default=0)
    lockout_until = Column(DateTime(timezone=True), nullable=True)
    password_reset_token = Column(String, nullable=True)
    password_reset_at = Column(DateTime(timezone=True), nullable=True)
    
    # Campos MFA
    mfa_enabled = Column(Boolean(), default=False)
    mfa_secret = Column(String, nullable=True)
    mfa_backup_codes = Column(JSON, nullable=True)
    mfa_last_used = Column(DateTime(timezone=True), nullable=True)
    mfa_attempts = Column(Integer, default=0)
    mfa_locked_until = Column(DateTime(timezone=True), nullable=True)

    # Campos de preferências
    preferences = Column(JSON, nullable=True)
    notification_settings = Column(JSON, nullable=True)
    api_key = Column(String, unique=True, nullable=True)
    api_key_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relacionamentos
    contents = relationship("Content", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    templates = relationship("Template", back_populates="user")
    generations = relationship("Generation", back_populates="user")

    def __repr__(self):
        return f"<User {self.email}>"
    
    def dict(self):
        """Converte o modelo para dicionário"""
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_login": self.last_login,
            "mfa_enabled": self.mfa_enabled,
            "preferences": self.preferences,
            "notification_settings": self.notification_settings
        } 