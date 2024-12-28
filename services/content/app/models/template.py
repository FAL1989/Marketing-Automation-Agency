from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from app.db.base_class import Base

class Template(Base):
    """
    Modelo para templates de geração de conteúdo
    """
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    template_type = Column(String, nullable=False)
    prompt_template = Column(String, nullable=False)
    default_params = Column(JSON, nullable=True, default={})
    template_metadata = Column(JSON, nullable=True, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    ) 