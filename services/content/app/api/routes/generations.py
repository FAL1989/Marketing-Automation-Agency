from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.generation import Generation
from app.schemas.content import Generation as GenerationSchema

router = APIRouter()

@router.get("/content/{content_id}", response_model=List[GenerationSchema])
def list_content_generations(
    content_id: int,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> List[Generation]:
    """
    Listar histórico de gerações de um conteúdo.
    """
    generations = db.query(Generation)\
        .filter(Generation.content_id == content_id)\
        .offset(skip)\
        .limit(limit)\
        .all()
    return generations

@router.get("/{generation_id}", response_model=GenerationSchema)
def get_generation(
    generation_id: int,
    db: Session = Depends(get_db),
) -> Generation:
    """
    Obter detalhes de uma geração específica.
    """
    generation = db.query(Generation).filter(Generation.id == generation_id).first()
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")
    return generation 