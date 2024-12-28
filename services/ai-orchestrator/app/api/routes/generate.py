from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from app.services.orchestrator import orchestrator
from app.core.config import settings

router = APIRouter()

class GenerateRequest(BaseModel):
    """Modelo de requisição para geração de conteúdo"""
    prompt: str = Field(..., description="Prompt para geração de conteúdo")
    provider: Optional[str] = Field(
        None,
        description="Provedor de IA específico (openai, anthropic, cohere)"
    )
    model: Optional[str] = Field(None, description="Modelo específico do provedor")
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

class GenerateResponse(BaseModel):
    """Modelo de resposta para geração de conteúdo"""
    content: str = Field(..., description="Conteúdo gerado")
    source: str = Field(..., description="Fonte do conteúdo (provedor ou cache)")
    cached: bool = Field(..., description="Indica se o conteúdo veio do cache")

async def get_user_id(x_user_id: str = Header(...)) -> str:
    """Extrai e valida o ID do usuário do header"""
    if not x_user_id:
        raise HTTPException(
            status_code=401,
            detail="Header X-User-Id é obrigatório"
        )
    return x_user_id

@router.post(
    "/generate",
    response_model=GenerateResponse,
    summary="Gera conteúdo usando IA",
    description="Gera conteúdo usando o melhor provedor de IA disponível"
)
async def generate_content(
    request: GenerateRequest,
    user_id: str = Depends(get_user_id)
) -> Dict[str, Any]:
    """
    Endpoint para geração de conteúdo usando IA
    """
    try:
        # Preparar parâmetros opcionais
        kwargs = {}
        if request.model:
            kwargs["model"] = request.model
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.max_tokens:
            kwargs["max_tokens"] = request.max_tokens
        
        # Gerar conteúdo
        result = await orchestrator.generate_content(
            prompt=request.prompt,
            user_id=user_id,
            provider=request.provider,
            **kwargs
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar conteúdo: {str(e)}"
        )

@router.get(
    "/usage/{provider}",
    summary="Obtém estatísticas de uso",
    description="Retorna estatísticas de uso do provedor especificado"
)
async def get_usage_stats(
    provider: str,
    user_id: str = Depends(get_user_id)
) -> Dict[str, Any]:
    """
    Endpoint para consulta de estatísticas de uso
    """
    if provider not in ["openai", "anthropic", "cohere"]:
        raise HTTPException(
            status_code=400,
            detail="Provedor inválido"
        )
    
    try:
        from app.core.rate_limiter import rate_limiter
        return await rate_limiter.get_usage_stats(user_id, provider)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter estatísticas: {str(e)}"
        ) 