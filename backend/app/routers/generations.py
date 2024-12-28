from fastapi import APIRouter, Depends
from ..core.security import get_current_user
from ..models.user import User

router = APIRouter()

@router.get("")
async def list_generations(current_user: User = Depends(get_current_user)):
    """Lista as gerações de conteúdo"""
    return [] 