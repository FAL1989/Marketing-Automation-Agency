from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship
from ..database.connection import Base

class User(Base):
    """Modelo de usuário"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    # Relacionamentos
    contents = relationship("Content", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    templates = relationship("Template", back_populates="user", lazy="dynamic") 