from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database.connection import Base

class Generation(Base):
    __tablename__ = "generations"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"))
    template_id = Column(Integer, ForeignKey("templates.id"))
    result = Column(Text)
    tokens_used = Column(Integer)
    cost = Column(Float)
    status = Column(String)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    generation_metadata = Column(JSON, nullable=True)

    # Relacionamentos
    content = relationship("Content", back_populates="generations", lazy="joined", single_parent=True)
    template = relationship("Template", back_populates="generations", lazy="joined", single_parent=True) 