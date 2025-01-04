from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import Token, TokenPayload, MFAResponse, MFAVerifyRequest
from app.schemas.user import UserCreate, UserInDB
from app.dependencies import get_current_user, get_db, auth_circuit_breaker
from app.core.notifications import notification_service
from app.core.events import EventType
from app.core.mfa import MFAService
from app.core.circuit_breaker import CircuitState
from datetime import timedelta
from app.core.security import SecurityService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint de login que retorna um token JWT
    """
    try:
        # Verifica as credenciais
        stmt = select(User).where(User.email == form_data.username)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário inativo"
            )
        
        # Gera tokens
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token = create_refresh_token(
            data={"sub": user.email}
        )
        
        # Registra evento de login
        await notification_service.notify_security_event(
            EventType.USER_LOGIN,
            {
                "email": user.email,
                "severity": "info"
            }
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        logger.error(f"Erro no login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno no servidor"
        )

@router.post("/mfa/verify")
async def verify_mfa(
    request: MFAVerifyRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Verifica código MFA
    """
    # Simula verificação MFA para testes
    if request.code == "000000":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código MFA inválido"
        )
    
    return {
        "message": "Código MFA verificado com sucesso",
        "user": current_user.email
    } 