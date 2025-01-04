from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class GenerationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class GenerationBase(BaseModel):
    """
    Atributos base para geração de conteúdo
    """
    prompt: str
    model: str
    parameters: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None

class GenerationCreate(GenerationBase):
    """
    Atributos para criar uma nova geração
    """
    pass

class GenerationUpdate(BaseModel):
    input_data: Optional[dict] = None
    settings: Optional[dict] = None

class Generation(GenerationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    owner_id: int
    status: GenerationStatus
    output: Optional[str] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True 

class GenerationResponse(GenerationBase):
    """
    Atributos retornados na resposta de uma geração
    """
    id: int
    user_id: int
    content: str
    status: str
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    metrics: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True 