from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.api.dependencies.database import get_db
from app.core.config import settings
from app.models.user import User
from app.services.user import user_service
from app.schemas.token import TokenPayload
from app.core.security import verify_token
from app.core.mfa import MFAService

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    try:
        user_id = verify_token(token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = user_service.get(db, id=int(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not user_service.is_active(current_user):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    if not user_service.is_superuser(current_user):
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user

async def verify_mfa_enabled(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> None:
    """
    Verifica se o usuário tem MFA habilitado.
    Levanta exceção se não tiver.
    """
    if not user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MFA não está habilitado para este usuário"
        )

async def verify_mfa_disabled(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> None:
    """
    Verifica se o usuário não tem MFA habilitado.
    Levanta exceção se tiver.
    """
    if user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MFA já está habilitado para este usuário"
        ) 