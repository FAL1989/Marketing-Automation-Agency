from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.dependencies.database import get_db
from app.api.dependencies.auth import get_current_user
from app.core.mfa import MFAService
from app.models.user import User
from pydantic import BaseModel

router = APIRouter()

class MFAVerifyRequest(BaseModel):
    code: str

class MFAResponse(BaseModel):
    message: str
    qr_uri: str = None

@router.post("/enable", response_model=MFAResponse)
async def enable_mfa(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Habilita autenticação de dois fatores para o usuário atual.
    Retorna URI para gerar QR code.
    """
    try:
        mfa_service = MFAService(db)
        uri = await mfa_service.enable_mfa(current_user)
        return {
            "message": "MFA habilitado com sucesso",
            "qr_uri": uri
        }
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
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
    mfa_service = MFAService(db)
    if await mfa_service.verify_mfa_code(current_user, request.code):
        return {"message": "Código MFA válido"}
    raise HTTPException(
        status_code=400,
        detail="Código MFA inválido"
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
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        ) 