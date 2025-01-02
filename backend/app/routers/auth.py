from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.security import create_access_token, create_refresh_token, verify_password
from ..core.config import settings
from ..models.user import User
from ..schemas.auth import Token, TokenPayload, MFAResponse, MFAVerifyRequest
from ..schemas.user import UserCreate, UserInDB
from ..dependencies import get_current_user, get_db, auth_circuit_breaker
from ..core.notifications import notification_service
from ..core.events import EventType
from ..core.mfa import MFAService
from ..core.circuit_breaker import CircuitState
from datetime import timedelta
from ..core.security import SecurityService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=Token)
async def register(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint de registro que cria um novo usuário e retorna um token JWT
    """
    try:
        # Verifica se o usuário já existe
        stmt = select(User).where(User.email == user_data.email)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já registrado"
            )
        
        # Cria o usuário
        security_service = SecurityService()
        user = User(
            email=user_data.email,
            hashed_password=security_service.get_password_hash(user_data.password),
            full_name=user_data.full_name,
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Gera os tokens
        access_token = create_access_token(
            data={"sub": user.email}
        )
        refresh_token = create_refresh_token(
            data={"sub": user.email}
        )
        
        await notification_service.notify_security_event(
            EventType.USER_CREATED,
            {
                "email": user.email,
                "ip": request.client.host,
                "user_agent": request.headers.get("user-agent"),
                "severity": "info"
            }
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await auth_circuit_breaker.record_failure(e)
        raise

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint de login que retorna um token JWT
    """
    if auth_circuit_breaker._state == CircuitState.OPEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço temporariamente indisponível"
        )
    
    try:
        stmt = select(User).where(User.email == form_data.username)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(form_data.password, user.hashed_password):
            error = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas",
                headers={"WWW-Authenticate": "Bearer"},
            )
            await auth_circuit_breaker.record_failure(error)
            await notification_service.notify_security_event(
                EventType.LOGIN_FAILED,
                {
                    "email": form_data.username,
                    "ip": request.client.host,
                    "user_agent": request.headers.get("user-agent"),
                    "severity": "warning"
                }
            )
            raise error
        
        access_token = create_access_token(
            data={"sub": user.email}
        )
        refresh_token = create_refresh_token(
            data={"sub": user.email}
        )
        
        await auth_circuit_breaker.record_success()
        await notification_service.notify_security_event(
            EventType.LOGIN_SUCCESS,
            {
                "email": user.email,
                "ip": request.client.host,
                "user_agent": request.headers.get("user-agent"),
                "severity": "info"
            }
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        await auth_circuit_breaker.record_failure(e)
        raise

@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para renovar o token de acesso usando um refresh token
    """
    try:
        access_token = create_access_token(
            data={"sub": current_user.email}
        )
        refresh_token = create_refresh_token(
            data={"sub": current_user.email}
        )
        
        await notification_service.notify_security_event(
            EventType.TOKEN_REFRESH,
            {
                "email": current_user.email,
                "ip": request.client.host,
                "user_agent": request.headers.get("user-agent"),
                "severity": "info"
            }
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        await auth_circuit_breaker.record_failure(e)
        raise

@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint de logout que invalida o token atual
    """
    try:
        await notification_service.notify_security_event(
            EventType.LOGOUT,
            {
                "email": current_user.email,
                "ip": request.client.host,
                "user_agent": request.headers.get("user-agent"),
                "severity": "info"
            }
        )
        
        return {"message": "Logout realizado com sucesso"}
        
    except Exception as e:
        await auth_circuit_breaker.record_failure(e)
        raise 

@router.post("/mfa/enable", response_model=MFAResponse)
async def enable_mfa(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para habilitar MFA para um usuário
    """
    try:
        mfa_service = MFAService(db)
        result = await mfa_service.enable_mfa(current_user)
        
        await notification_service.notify_security_event(
            EventType.MFA_ENABLED,
            {
                "email": current_user.email,
                "ip": request.client.host,
                "user_agent": request.headers.get("user-agent"),
                "severity": "info"
            }
        )
        
        return result
        
    except Exception as e:
        await auth_circuit_breaker.record_failure(e)
        raise

@router.post("/mfa/verify")
async def verify_mfa(
    request: Request,
    mfa_data: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para verificar um código MFA
    """
    logger.info(f"Iniciando verificação MFA para usuário: {current_user.email}")
    
    try:
        mfa_service = MFAService(db)
        result = await mfa_service.verify_mfa(current_user, mfa_data.code)
        
        if result:
            await notification_service.notify_security_event(
                EventType.MFA_VERIFIED,
                {
                    "email": current_user.email,
                    "ip": request.client.host,
                    "user_agent": request.headers.get("user-agent"),
                    "severity": "info"
                }
            )
            
            return {"message": "Código MFA verificado com sucesso"}
        else:
            await notification_service.notify_security_event(
                EventType.MFA_FAILED,
                {
                    "email": current_user.email,
                    "ip": request.client.host,
                    "user_agent": request.headers.get("user-agent"),
                    "severity": "warning"
                }
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Código MFA inválido"
            )
            
    except Exception as e:
        await auth_circuit_breaker.record_failure(e)
        raise 