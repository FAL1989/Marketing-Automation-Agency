from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.dependencies.database import get_db
from app.api.dependencies.auth import get_current_user
from app.schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateUse
)
from app.services.template import template_service

router = APIRouter()

@router.post(
    "/templates",
    response_model=TemplateResponse,
    summary="Cria novo template",
    description="Cria um novo template para geração de conteúdo"
)
async def create_template(
    template_in: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> TemplateResponse:
    """
    Cria novo template
    """
    try:
        template = await template_service.create_template(
            db=db,
            user_id=current_user["id"],
            template_data=template_in
        )
        return template
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get(
    "/templates",
    response_model=List[TemplateResponse],
    summary="Lista templates",
    description="Lista todos os templates do usuário"
)
def list_templates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> List[TemplateResponse]:
    """
    Lista templates do usuário
    """
    templates = template_service.list_templates(
        db=db,
        user_id=current_user["id"],
        skip=skip,
        limit=limit
    )
    return templates

@router.get(
    "/templates/{template_id}",
    response_model=TemplateResponse,
    summary="Obtém template",
    description="Obtém um template específico do usuário"
)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> TemplateResponse:
    """
    Obtém template por ID
    """
    template = template_service.get_template(
        db=db,
        template_id=template_id,
        user_id=current_user["id"]
    )
    if not template:
        raise HTTPException(
            status_code=404,
            detail="Template não encontrado"
        )
    return template

@router.put(
    "/templates/{template_id}",
    response_model=TemplateResponse,
    summary="Atualiza template",
    description="Atualiza um template existente"
)
async def update_template(
    template_id: int,
    template_in: TemplateUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> TemplateResponse:
    """
    Atualiza template existente
    """
    try:
        template = await template_service.update_template(
            db=db,
            template_id=template_id,
            user_id=current_user["id"],
            template_data=template_in
        )
        if not template:
            raise HTTPException(
                status_code=404,
                detail="Template não encontrado"
            )
        return template
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.delete(
    "/templates/{template_id}",
    summary="Remove template",
    description="Remove um template existente"
)
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Remove template existente
    """
    try:
        deleted = await template_service.delete_template(
            db=db,
            template_id=template_id,
            user_id=current_user["id"]
        )
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Template não encontrado"
            )
        return {"message": "Template removido com sucesso"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post(
    "/templates/use",
    summary="Usa template",
    description="Usa um template para gerar conteúdo"
)
async def use_template(
    template_use: TemplateUse,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Usa template para gerar conteúdo
    """
    try:
        result = await template_service.use_template(
            db=db,
            user_id=current_user["id"],
            template_use=template_use
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        ) 