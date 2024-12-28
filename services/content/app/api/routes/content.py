from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.dependencies.database import get_db
from app.api.dependencies.auth import get_current_user
from app.schemas.content import ContentCreate, ContentUpdate, ContentResponse
from app.services.content import content_service
from app.services.ai_client import ai_client

router = APIRouter()

@router.post(
    "/contents",
    response_model=ContentResponse,
    summary="Cria novo conteúdo",
    description="Cria novo conteúdo, opcionalmente gerando texto via IA"
)
async def create_content(
    content_in: ContentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> ContentResponse:
    """
    Cria novo conteúdo
    """
    try:
        content = await content_service.create_content(
            db=db,
            user_id=current_user["id"],
            content_data=content_in
        )
        return content
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get(
    "/contents",
    response_model=List[ContentResponse],
    summary="Lista conteúdos",
    description="Lista todos os conteúdos do usuário"
)
def list_contents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> List[ContentResponse]:
    """
    Lista conteúdos do usuário
    """
    contents = content_service.list_contents(
        db=db,
        user_id=current_user["id"],
        skip=skip,
        limit=limit
    )
    return contents

@router.get(
    "/contents/{content_id}",
    response_model=ContentResponse,
    summary="Obtém conteúdo",
    description="Obtém um conteúdo específico do usuário"
)
def get_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> ContentResponse:
    """
    Obtém conteúdo por ID
    """
    content = content_service.get_content(
        db=db,
        content_id=content_id,
        user_id=current_user["id"]
    )
    if not content:
        raise HTTPException(
            status_code=404,
            detail="Conteúdo não encontrado"
        )
    return content

@router.put(
    "/contents/{content_id}",
    response_model=ContentResponse,
    summary="Atualiza conteúdo",
    description="Atualiza um conteúdo existente, opcionalmente gerando novo texto via IA"
)
async def update_content(
    content_id: int,
    content_in: ContentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> ContentResponse:
    """
    Atualiza conteúdo existente
    """
    try:
        content = await content_service.update_content(
            db=db,
            content_id=content_id,
            user_id=current_user["id"],
            content_data=content_in
        )
        if not content:
            raise HTTPException(
                status_code=404,
                detail="Conteúdo não encontrado"
            )
        return content
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.delete(
    "/contents/{content_id}",
    summary="Remove conteúdo",
    description="Remove um conteúdo existente"
)
async def delete_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Remove conteúdo existente
    """
    try:
        deleted = await content_service.delete_content(
            db=db,
            content_id=content_id,
            user_id=current_user["id"]
        )
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Conteúdo não encontrado"
            )
        return {"message": "Conteúdo removido com sucesso"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get(
    "/contents/usage/{provider}",
    summary="Obtém estatísticas de uso",
    description="Obtém estatísticas de uso do provedor de IA especificado"
)
async def get_usage_stats(
    provider: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Obtém estatísticas de uso do provedor
    """
    try:
        return await ai_client.get_usage_stats(
            user_id=str(current_user["id"]),
            provider=provider
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        ) 