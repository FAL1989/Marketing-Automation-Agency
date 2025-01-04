from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import get_current_user
from app.schemas.user import User

router = APIRouter()

@router.get("/resource")
async def protected_resource(current_user: User = Depends(get_current_user)):
    """
    Endpoint protegido para testes
    """
    return {
        "message": "Acesso permitido",
        "user": current_user.email
    } 