from sqlalchemy import Boolean, Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database.connection import Base

class Template(Base):
    """Modelo de template"""
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    content = Column(String)
    parameters = Column(JSON, default=list)
    is_public = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    user_id = Column(Integer, ForeignKey("users.id"))

    # Relacionamentos
    user = relationship("User", back_populates="templates")
    generations = relationship("Generation", back_populates="template", cascade="all, delete-orphan", passive_deletes=True) 