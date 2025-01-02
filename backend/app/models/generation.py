from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..db.base_class import Base

class Generation(Base):
    """Modelo de geração de conteúdo"""
    __tablename__ = "generations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content_id = Column(Integer, ForeignKey("contents.id", ondelete="SET NULL"), nullable=True)
    template_id = Column(Integer, ForeignKey("templates.id", ondelete="SET NULL"), nullable=True)
    result = Column(Text)
    tokens_used = Column(Integer)
    cost = Column(Float)
    status = Column(String)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    generation_metadata = Column(Text, nullable=True)

    # Relacionamentos
    user = relationship("User", back_populates="generations", lazy="joined")
    content = relationship("Content", back_populates="generations", lazy="joined", single_parent=True)
    template = relationship("Template", back_populates="generations", lazy="joined", single_parent=True) 