from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..core.security import get_current_user
from ..models.user import User
from ..models.template import Template
from ..schemas.template import TemplateCreate, TemplateUpdate, Template as TemplateSchema
from ..database.connection import get_db

router = APIRouter()

@router.post("", response_model=TemplateSchema)
async def create_template(
    template: TemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cria um novo template"""
    db_template = Template(
        name=template.name,
        description=template.description,
        content=template.content,
        parameters=template.parameters,
        is_public=template.is_public,
        user_id=current_user.id
    )
    db.add(db_template)
    try:
        db.commit()
        db.refresh(db_template)
        return db_template
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("", response_model=List[TemplateSchema])
async def list_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista os templates disponíveis"""
    templates = db.query(Template).filter(
        (Template.user_id == current_user.id) | 
        (Template.is_public == True)
    ).all()
    return templates

@router.get("/{template_id}", response_model=TemplateSchema)
async def get_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtém um template específico"""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    if not template.is_public and template.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso não autorizado")
    return template

@router.put("/{template_id}", response_model=TemplateSchema)
async def update_template(
    template_id: int,
    template_update: TemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualiza um template existente"""
    db_template = db.query(Template).filter(Template.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    if db_template.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso não autorizado")
    
    update_data = template_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_template, field, value)
    
    try:
        db.commit()
        db.refresh(db_template)
        return db_template
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove um template existente"""
    db_template = db.query(Template).filter(Template.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    if db_template.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso não autorizado")
    
    try:
        db.delete(db_template)
        db.commit()
        return {"message": "Template removido com sucesso"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 