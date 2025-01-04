from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_current_user, get_db
from app.core.security import get_password_hash
from app.crud.user import user as crud_user
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserInDB, UserOut
from sqlalchemy import select
from app.core.notifications import notification_service
from app.core.events import EventType

router = APIRouter()

@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate
) -> UserOut:
    """
    Cria um novo usuário.
    """
    # Verifica se já existe usuário com este email
    user = await crud_user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Cria o usuário
    user = await crud_user.create(
        db,
        obj_in=UserCreate(
            email=user_in.email,
            password=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            is_active=True,
            is_superuser=False
        )
    )
    await notification_service.notify_security_event(
        EventType.USER_CREATED,
        {
            "email": user.email,
            "severity": "info"
        }
    )
    return user

@router.get("", response_model=List[UserOut])
async def list_users(
    *,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
) -> List[UserOut]:
    """
    Lista todos os usuários.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    users = await crud_user.get_multi(db, skip=skip, limit=limit)
    return users

@router.get("/me", response_model=UserOut)
async def read_user_me(
    current_user: User = Depends(get_current_user)
) -> UserOut:
    """
    Obtém o usuário logado.
    """
    return current_user

@router.get("/{user_id}", response_model=UserOut)
async def read_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: int,
    current_user: User = Depends(get_current_user)
) -> UserOut:
    """
    Obtém um usuário específico.
    """
    user = await crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return user

@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user)
) -> UserOut:
    """
    Atualiza um usuário.
    """
    user = await crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    user = await crud_user.update(db, db_obj=user, obj_in=user_in)
    await notification_service.notify_security_event(
        EventType.USER_UPDATED,
        {
            "email": user.email,
            "severity": "info"
        }
    )
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: int,
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Deleta um usuário.
    """
    user = await crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    await crud_user.remove(db, id=user_id)
    await notification_service.notify_security_event(
        EventType.USER_DELETED,
        {
            "email": user.email,
            "severity": "info"
        }
    ) 