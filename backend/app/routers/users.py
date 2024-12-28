from fastapi import APIRouter, Depends, HTTPException, status
from ..core.config import settings

router = APIRouter()

@router.get("/me")
async def get_current_user():
    """Endpoint para obter informações do usuário atual"""
    # TODO: Implementar lógica de usuário
    return {"message": "User info endpoint"} 