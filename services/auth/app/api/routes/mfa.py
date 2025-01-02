from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.api.dependencies.database import get_db
from app.api.dependencies.auth import get_current_user
from app.core.mfa import MFAService, MFAError, MFALockedException
from app.models.user import User
from app.services.email import EmailService
from pydantic import BaseModel, EmailStr
from typing import List, Optional

router = APIRouter()

class MFAVerifyRequest(BaseModel):
    code: str

class MFAResponse(BaseModel):
    message: str
    qr_uri: Optional[str] = None
    backup_codes: Optional[List[str]] = None

class MFARecoveryRequest(BaseModel):
    recovery_email: EmailStr

@router.post("/enable", response_model=MFAResponse)
async def enable_mfa(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Habilita autenticação de dois fatores para o usuário atual.
    Retorna URI para gerar QR code e códigos de backup.
    """
    try:
        mfa_service = MFAService(db)
        mfa_data = await mfa_service.enable_mfa(current_user)
        
        # Envia códigos de backup por email
        email_service = EmailService()
        background_tasks.add_task(
            email_service.send_backup_codes,
            current_user.email,
            mfa_data["backup_codes"]
        )
        
        return {
            "message": "MFA habilitado com sucesso",
            "qr_uri": mfa_data["uri"],
            "backup_codes": mfa_data["backup_codes"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao habilitar MFA: {str(e)}"
        )

@router.post("/verify", response_model=MFAResponse)
async def verify_mfa(
    request: MFAVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verifica um código MFA fornecido pelo usuário.
    """
    try:
        mfa_service = MFAService(db)
        if await mfa_service.verify_mfa_code(current_user, request.code):
            return {"message": "Código MFA válido"}
        raise HTTPException(
            status_code=400,
            detail="Código MFA inválido"
        )
    except MFALockedException as e:
        raise HTTPException(
            status_code=429,
            detail=str(e)
        )
    except MFAError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao verificar código MFA: {str(e)}"
        )

@router.post("/disable", response_model=MFAResponse)
async def disable_mfa(
    request: MFAVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Desabilita MFA para o usuário atual.
    Requer código MFA válido para confirmar.
    """
    try:
        mfa_service = MFAService(db)
        if not await mfa_service.verify_mfa_code(current_user, request.code):
            raise HTTPException(
                status_code=400,
                detail="Código MFA inválido"
            )
            
        await mfa_service.disable_mfa(current_user)
        return {"message": "MFA desabilitado com sucesso"}
    except MFALockedException as e:
        raise HTTPException(
            status_code=429,
            detail=str(e)
        )
    except MFAError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao desabilitar MFA: {str(e)}"
        )

@router.post("/recovery-email", response_model=MFAResponse)
async def set_recovery_email(
    request: MFARecoveryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Define email de recuperação para MFA
    """
    try:
        current_user.mfa_recovery_email = request.recovery_email
        db.commit()
        return {"message": "Email de recuperação definido com sucesso"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao definir email de recuperação: {str(e)}"
        )

@router.post("/reset-attempts", response_model=MFAResponse)
async def reset_mfa_attempts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reseta contador de tentativas falhas de MFA
    """
    try:
        mfa_service = MFAService(db)
        await mfa_service.reset_mfa_attempts(current_user)
        return {"message": "Contador de tentativas resetado com sucesso"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao resetar tentativas: {str(e)}"
        ) 