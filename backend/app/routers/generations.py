from fastapi import APIRouter, Depends, HTTPException
from ..dependencies import get_current_user
from ..models.user import User
from ..models.generation import Generation
from ..schemas.generation import GenerationCreate, GenerationResponse
from ..services.generation_service import GenerationService
from typing import List

router = APIRouter()

@router.post("/", response_model=GenerationResponse)
async def create_generation(
    generation: GenerationCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Cria uma nova geração de conteúdo
    """
    service = GenerationService()
    return await service.create_generation(generation, current_user)

@router.get("/", response_model=List[GenerationResponse])
async def list_generations(
    current_user: User = Depends(get_current_user)
):
    """
    Lista todas as gerações do usuário atual
    """
    service = GenerationService()
    return await service.list_generations(current_user)

@router.get("/{generation_id}", response_model=GenerationResponse)
async def get_generation(
    generation_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Obtém uma geração específica
    """
    service = GenerationService()
    generation = await service.get_generation(generation_id, current_user)
    if not generation:
        raise HTTPException(status_code=404, detail="Geração não encontrada")
    return generation 