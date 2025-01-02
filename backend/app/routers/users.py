from fastapi import APIRouter, Depends, HTTPException, status, Request
from ..core.security import get_password_hash
from ..core.config import settings
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate, UserInDB, UserOut
from ..dependencies import get_current_user, get_db, auth_circuit_breaker
from ..core.notifications import notification_service
from ..core.events import EventType
from sqlalchemy.orm import Session
from typing import List
import re
import logging

router = APIRouter(prefix="/users", tags=["users"])

def validate_password_strength(password: str) -> bool:
    """
    Valida a força da senha
    """
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True

def validate_email(email: str) -> bool:
    """
    Valida o formato do email
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))

@router.get("/me", response_model=UserOut)
async def read_users_me(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Retorna os dados do usuário atual
    """
    try:
        # Se chegou aqui, o usuário está autenticado, então podemos notificar
        await notification_service.notify_security_event(
            EventType.USER_UPDATED,
            {
                "email": current_user.email,
                "ip": request.client.host,
                "user_agent": request.headers.get("user-agent"),
                "action": "read_profile",
                "severity": "info"
            }
        )
        return current_user
    except Exception as e:
        logger.error(f"Erro ao acessar perfil: {str(e)}")
        raise

@router.post("/register", response_model=UserOut)
async def register_user(
    request: Request,
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Registra um novo usuário
    """
    # Valida o email
    if not validate_email(user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de email inválido"
        )
    
    # Valida a força da senha
    if not validate_password_strength(user_in.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A senha deve ter pelo menos 8 caracteres, incluindo maiúsculas, minúsculas, números e caracteres especiais"
        )
    
    # Verifica se o email já está em uso
    if db.query(User).filter(User.email == user_in.email).first():
        await notification_service.notify_security_event(
            EventType.USER_CREATED,
            {
                "email": user_in.email,
                "ip": request.client.host,
                "user_agent": request.headers.get("user-agent"),
                "status": "failed",
                "reason": "email_exists",
                "severity": "warning"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já está em uso"
        )
    
    # Cria o usuário
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    await notification_service.notify_security_event(
        EventType.USER_CREATED,
        {
            "email": user.email,
            "ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "status": "success",
            "severity": "info"
        }
    )
    
    return user

@router.put("/me", response_model=UserOut)
async def update_user_me(
    request: Request,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Atualiza os dados do usuário atual
    """
    if user_in.password:
        if not validate_password_strength(user_in.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A senha deve ter pelo menos 8 caracteres, incluindo maiúsculas, minúsculas, números e caracteres especiais"
            )
        current_user.hashed_password = get_password_hash(user_in.password)
        
        await notification_service.notify_security_event(
            EventType.PASSWORD_CHANGED,
            {
                "email": current_user.email,
                "ip": request.client.host,
                "user_agent": request.headers.get("user-agent"),
                "severity": "info"
            }
        )
    
    if user_in.full_name:
        current_user.full_name = user_in.full_name
    
    if user_in.email:
        if not validate_email(user_in.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de email inválido"
            )
        # Verifica se o novo email já está em uso
        if db.query(User).filter(User.email == user_in.email).first():
            await notification_service.notify_security_event(
                EventType.USER_UPDATED,
                {
                    "email": current_user.email,
                    "ip": request.client.host,
                    "user_agent": request.headers.get("user-agent"),
                    "status": "failed",
                    "reason": "email_exists",
                    "severity": "warning"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já está em uso"
            )
        current_user.email = user_in.email
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    await notification_service.notify_security_event(
        EventType.USER_UPDATED,
        {
            "email": current_user.email,
            "ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "status": "success",
            "severity": "info"
        }
    )
    
    return current_user

@router.post("/profile", response_model=UserOut)
async def update_profile(
    request: Request,
    profile_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Atualiza o perfil do usuário
    """
    # Validação contra XSS
    for key, value in profile_data.items():
        if isinstance(value, str):
            # Verifica scripts maliciosos
            if any(script in value.lower() for script in ["<script>", "javascript:", "onerror=", "onload="]):
                await notification_service.notify_security_event(
                    EventType.SUSPICIOUS_ACTIVITY,
                    {
                        "email": current_user.email,
                        "ip": request.client.host,
                        "user_agent": request.headers.get("user-agent"),
                        "action": "update_profile",
                        "reason": "xss_attempt",
                        "severity": "high"
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Conteúdo não permitido detectado"
                )
            
            # Sanitiza o valor
            value = value.replace("<", "&lt;").replace(">", "&gt;")
            profile_data[key] = value
    
    # Atualiza os campos do perfil
    for key, value in profile_data.items():
        if hasattr(current_user, key):
            setattr(current_user, key, value)
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    await notification_service.notify_security_event(
        EventType.USER_UPDATED,
        {
            "email": current_user.email,
            "ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "action": "update_profile",
            "severity": "info"
        }
    )
    
    return current_user 

@router.post("/", response_model=UserOut)
async def create_user(
    request: Request,
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Cria um novo usuário
    """
    return await register_user(request, user_in, db) 