from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base

class Generation(Base):
    __tablename__ = "generations"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"))
    result = Column(Text)
    tokens_used = Column(Integer)
    cost = Column(Float)
    status = Column(String)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    generation_metadata = Column(Text)  # JSON com metadados da geração

    # Relacionamentos
    content = relationship("Content", back_populates="generations") 