from sqlalchemy import Boolean, Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from app.db.base_class import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(String, default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Campos MFA
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String, nullable=True)
    mfa_backup_codes = Column(JSON, nullable=True)  # Lista de códigos de backup hasheados
    mfa_last_used = Column(DateTime(timezone=True), nullable=True)  # Último uso do MFA
    mfa_recovery_email = Column(String, nullable=True)  # Email alternativo para recuperação
    mfa_attempts = Column(Integer, default=0)  # Contador de tentativas falhas
    mfa_locked_until = Column(DateTime(timezone=True), nullable=True)  # Bloqueio temporário após muitas tentativas
    last_login = Column(DateTime(timezone=True), nullable=True) 