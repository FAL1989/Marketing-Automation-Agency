from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class GenerationBase(BaseModel):
    result: Optional[str] = None
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    status: str
    error_message: Optional[str] = None
    generation_metadata: Optional[dict] = None

class GenerationCreate(GenerationBase):
    content_id: int

class Generation(GenerationBase):
    id: int
    content_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ContentBase(BaseModel):
    title: str
    prompt: str
    parameters: Optional[dict] = None
    model: str = "gpt-3.5-turbo"

class ContentCreate(ContentBase):
    pass

class ContentUpdate(BaseModel):
    title: Optional[str] = None
    prompt: Optional[str] = None
    parameters: Optional[dict] = None
    model: Optional[str] = None
    status: Optional[str] = None

class Content(ContentBase):
    id: int
    result: Optional[str] = None
    status: str
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    generations: List[Generation] = []

    class Config:
        from_attributes = True