from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class TemplateBase(BaseModel):
    """Schema base para template"""
    name: str = Field(..., description="Nome do template")
    description: Optional[str] = Field(None, description="Descrição do template")
    template_type: str = Field(..., description="Tipo do template")
    prompt_template: str = Field(..., description="Template do prompt")
    default_params: Optional[Dict[str, Any]] = Field(
        default={},
        description="Parâmetros padrão do template"
    )
    template_metadata: Optional[Dict[str, Any]] = Field(
        default={},
        description="Metadados adicionais do template"
    )

class TemplateCreate(TemplateBase):
    """Schema para criação de template"""
    user_id: int = Field(..., description="ID do usuário que criou o template")

class TemplateUpdate(TemplateBase):
    """Schema para atualização de template"""
    name: Optional[str] = None
    prompt_template: Optional[str] = None
    template_type: Optional[str] = None

class TemplateInDBBase(TemplateBase):
    """Schema para template no banco de dados"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Template(TemplateInDBBase):
    """Schema para template no banco de dados"""
    pass

class TemplateInDB(TemplateInDBBase):
    """Schema para template no banco de dados"""
    pass

class TemplateResponse(TemplateInDB):
    """Schema para resposta da API"""
    pass

class TemplateUse(BaseModel):
    """Schema para uso do template"""
    template_id: int = Field(..., description="ID do template a ser usado")
    variables: Dict[str, Any] = Field(
        ...,
        description="Variáveis para substituir no template"
    )
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