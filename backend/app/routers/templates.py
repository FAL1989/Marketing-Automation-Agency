from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..dependencies import get_current_user
from ..models.user import User
from ..models.template import Template
from ..schemas.template import TemplateCreate, TemplateUpdate, Template as TemplateSchema
from ..db.deps import get_db

router = APIRouter(
    prefix="/templates",
    tags=["templates"]
)

@router.post("", response_model=TemplateSchema)
async def create_template(
    template: TemplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cria um novo template
    """
    # Verifica se já existe um template com o mesmo nome para o usuário
    existing_template = await db.execute(
        "SELECT * FROM templates WHERE name = %s AND user_id = %s",
        (template.name, current_user.id)
    )
    existing_template = existing_template.fetchone()
    
    if existing_template:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template com este nome já existe"
        )
    
    db_template = Template(**template.dict(), user_id=current_user.id)
    db.add(db_template)
    await db.commit()
    await db.refresh(db_template)
    return db_template

@router.get("", response_model=List[TemplateSchema])
async def list_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todos os templates do usuário
    """
    templates = await db.execute(
        "SELECT * FROM templates WHERE user_id = %s",
        (current_user.id,)
    )
    templates = templates.fetchall()
    return [TemplateSchema(**template) for template in templates]

@router.get("/{template_id}", response_model=TemplateSchema)
async def get_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtém um template específico
    """
    template = await db.execute(
        "SELECT * FROM templates WHERE id = %s AND user_id = %s",
        (template_id, current_user.id)
    )
    template = template.fetchone()
    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    return TemplateSchema(**template)

@router.put("/{template_id}", response_model=TemplateSchema)
async def update_template(
    template_id: int,
    template_update: TemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Atualiza um template existente
    """
    template = await db.execute(
        "SELECT * FROM templates WHERE id = %s AND user_id = %s",
        (template_id, current_user.id)
    )
    template = template.fetchone()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    
    # Verifica se o novo nome já existe (se o nome estiver sendo atualizado)
    if template_update.name and template_update.name != template['name']:
        existing_template = await db.execute(
            "SELECT * FROM templates WHERE name = %s AND user_id = %s AND id != %s",
            (template_update.name, current_user.id, template_id)
        )
        existing_template = existing_template.fetchone()
        
        if existing_template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Template com este nome já existe"
            )
    
    for field, value in template_update.dict(exclude_unset=True).items():
        setattr(template, field, value)
    
    await db.commit()
    await db.refresh(template)
    return TemplateSchema(**template)

@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove um template
    """
    template = await db.execute(
        "SELECT * FROM templates WHERE id = %s AND user_id = %s",
        (template_id, current_user.id)
    )
    template = template.fetchone()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    
    await db.execute("DELETE FROM templates WHERE id = %s", (template_id,))
    await db.commit()
    return {"message": "Template removido com sucesso"} 