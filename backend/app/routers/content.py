from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import random
import asyncio
import logging

from ..db.deps import get_db
from ..services.content_service import ContentService
from ..schemas.content import Content, ContentCreate, ContentUpdate
from ..dependencies import get_current_user
from ..models.user import User
from ..models.template import Template
from ..core.config import settings
from ..models.content import Content as ContentModel

router = APIRouter(prefix="/contents", tags=["contents"])
logger = logging.getLogger(__name__)

# Singleton global do ContentService
_content_service = ContentService()

async def get_content_service() -> ContentService:
    """Dependência para obter uma instância do ContentService"""
    try:
        await _content_service.ensure_initialized()
        return _content_service
    except Exception as e:
        logger.error(f"Failed to get ContentService: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Service temporarily unavailable. Please try again later."
        )

@router.post("/", response_model=Content)
async def create_content(
    content: ContentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    content_service: ContentService = Depends(get_content_service)
):
    """
    Cria um novo conteúdo para geração.
    """
    # Validar parâmetros
    if content.parameters:
        provider = content.parameters.get("provider", settings.DEFAULT_PROVIDER)
        if provider not in ["openai", "anthropic", "cohere"]:
            raise HTTPException(
                status_code=400,
                detail="Provider inválido. Use 'openai', 'anthropic' ou 'cohere'"
            )
        
        model = content.model or settings.DEFAULT_MODEL
        if not model:
            raise HTTPException(
                status_code=400,
                detail="Modelo não especificado"
            )
    
    return await content_service.create_content(
        db=db,
        user_id=current_user.id,
        title=content.title,
        prompt=content.prompt,
        parameters=content.parameters,
        model=content.model
    )

@router.post("/{content_id}/generate", response_model=Content)
async def generate_content(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    content_service: ContentService = Depends(get_content_service)
):
    """
    Inicia o processo de geração de conteúdo usando o AIOrchestrator.
    """
    # Verificar se o conteúdo existe e pertence ao usuário
    content = db.query(ContentModel).filter(
        ContentModel.id == content_id,
        ContentModel.user_id == current_user.id
    ).first()
    
    if not content:
        raise HTTPException(
            status_code=404,
            detail="Conteúdo não encontrado ou sem permissão"
        )
    
    # Verificar se o conteúdo já está em geração
    if content.status == "generating":
        raise HTTPException(
            status_code=400,
            detail="Conteúdo já está em processo de geração"
        )
    
    return await content_service.generate_content(db=db, content_id=content_id)

@router.get("/", response_model=List[Content])
async def list_contents(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    content_service: ContentService = Depends(get_content_service)
):
    """
    Lista todos os conteúdos do usuário atual.
    """
    return await content_service.list_contents(db=db, user_id=current_user.id, skip=skip, limit=limit)

@router.get("/{content_id}", response_model=Content)
async def get_content(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    content_service: ContentService = Depends(get_content_service)
):
    """
    Retorna um conteúdo específico.
    """
    content = db.query(ContentModel).filter(
        ContentModel.id == content_id,
        ContentModel.user_id == current_user.id
    ).first()
    
    if not content:
        raise HTTPException(
            status_code=404,
            detail="Conteúdo não encontrado ou sem permissão"
        )
    
    return content

@router.put("/{content_id}", response_model=Content)
async def update_content(
    content_id: int,
    content_update: ContentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    content_service: ContentService = Depends(get_content_service)
):
    """
    Atualiza um conteúdo existente.
    """
    return await content_service.update_content(
        db=db,
        content_id=content_id,
        title=content_update.title,
        prompt=content_update.prompt,
        parameters=content_update.parameters
    )

@router.delete("/{content_id}")
async def delete_content(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    content_service: ContentService = Depends(get_content_service)
):
    """
    Remove um conteúdo existente.
    """
    await content_service.delete_content(db=db, content_id=content_id)
    return {"message": "Content deleted successfully"}

@router.get("/slow-endpoint")
async def slow_endpoint(current_user: User = Depends(get_current_user)):
    """
    Endpoint lento para testar o circuit breaker.
    Simula latência e falhas aleatórias.
    """
    # Simula latência aleatória entre 1 e 10 segundos
    delay = random.uniform(1, 10)
    
    # 30% de chance de falha
    if random.random() < 0.3:
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
    
    await asyncio.sleep(delay)
    return {"message": "Slow response completed", "delay": delay}

@router.post("/generate")
async def generate_content(
    template_id: int,
    parameters: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    content_service: ContentService = Depends(get_content_service)
):
    """
    Gera conteúdo baseado em um template e parâmetros usando a OpenAI.
    """
    try:
        # Busca o template
        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Template não encontrado")

        # Substitui os parâmetros no conteúdo do template
        prompt = template.content
        for key, value in parameters.items():
            placeholder = f"{{{key}}}"
            prompt = prompt.replace(placeholder, str(value))

        # Cria o conteúdo
        content = ContentModel(
            prompt=prompt,
            parameters={"temperature": 0.7, "max_tokens": 2000},  # Parâmetros padrão para a OpenAI
            model="gpt-3.5-turbo",
            user_id=current_user.id,
            status="pending"
        )
        db.add(content)
        db.commit()
        db.refresh(content)

        # Gera o conteúdo usando a OpenAI
        result = await content_service.generate_content(db, content.id, template_id)
        return result

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        ) 