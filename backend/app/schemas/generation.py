from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class GenerationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class GenerationBase(BaseModel):
    template_id: int
    input_data: dict = Field(..., description="Dados de entrada para a geração")
    settings: Optional[dict] = Field(default_factory=dict, description="Configurações adicionais")

class GenerationCreate(GenerationBase):
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