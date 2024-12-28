from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ContentBase(BaseModel):
    """Schema base para conteúdo"""
    title: str = Field(..., description="Título do conteúdo")
    text: Optional[str] = Field(None, description="Texto do conteúdo")
    content_type: str = Field(..., description="Tipo do conteúdo")
    content_metadata: Optional[Dict[str, Any]] = Field(default={}, description="Metadados adicionais")

class ContentCreate(ContentBase):
    """Schema para criação de conteúdo"""
    prompt: Optional[str] = Field(None, description="Prompt para geração de conteúdo")
    ai_provider: Optional[str] = Field(None, description="Provedor de IA a ser usado")
    ai_model: Optional[str] = Field(None, description="Modelo específico do provedor")
    temperature: Optional[float] = Field(
        None,
        description="Temperatura para geração (0.0 a 1.0)",
        ge=0.0,
        le=1.0
    )
    max_tokens: Optional[int] = Field(
        None,
        description="Número máximo de tokens a gerar",
        gt=0
    )
    user_id: int = Field(..., description="ID do usuário que criou o conteúdo")

class ContentUpdate(ContentBase):
    """Schema para atualização de conteúdo"""
    title: Optional[str] = None
    prompt: Optional[str] = Field(None, description="Prompt para geração de conteúdo")
    ai_provider: Optional[str] = Field(None, description="Provedor de IA a ser usado")
    ai_model: Optional[str] = Field(None, description="Modelo específico do provedor")
    temperature: Optional[float] = Field(
        None,
        description="Temperatura para geração (0.0 a 1.0)",
        ge=0.0,
        le=1.0
    )
    max_tokens: Optional[int] = Field(
        None,
        description="Número máximo de tokens a gerar",
        gt=0
    )

class ContentInDBBase(ContentBase):
    """Schema para conteúdo no banco de dados"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ContentResponse(ContentInDBBase):
    """Schema para resposta da API"""
    pass

class Content(ContentInDBBase):
    """Schema para resposta da API"""
    pass

class ContentInDB(ContentInDBBase):
    """Schema para conteúdo no banco de dados"""
    pass