from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database.connection import Base

class Content(Base):
    """Modelo de conteúdo gerado"""
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(String)
    generated_text = Column(String)
    model = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))

    # Relacionamentos
    user = relationship("User", back_populates="contents")
    generations = relationship("Generation", back_populates="content", lazy="dynamic", cascade="all, delete-orphan", passive_deletes=True) 