from pydantic import BaseModel, Field
from typing import Dict, Optional, List
from datetime import datetime

class TemplateParameter(BaseModel):
    name: str
    label: Optional[str] = None
    type: str = Field(..., pattern="^(text|number|select)$")
    description: Optional[str] = None
    required: bool = False
    placeholder: Optional[str] = None
    options: Optional[List[str]] = None

class TemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    content: str
    parameters: List[TemplateParameter] = Field(default_factory=list)
    is_public: bool = False

class TemplateCreate(TemplateBase):
    pass

class TemplateUpdate(TemplateBase):
    name: Optional[str] = None
    content: Optional[str] = None
    is_active: Optional[bool] = None

class Template(TemplateBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 