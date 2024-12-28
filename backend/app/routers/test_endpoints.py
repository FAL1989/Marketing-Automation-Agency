from fastapi import APIRouter, Depends
from ..dependencies import get_current_user

router = APIRouter()

@router.get("/api/test")
async def api_test():
    """Endpoint de teste da API"""
    return {"message": "API test endpoint"}

@router.get("/public/test")
async def public_test():
    """Endpoint público de teste"""
    return {"message": "Public test endpoint"}

@router.get("/protected/test")
async def protected_test(current_user = Depends(get_current_user)):
    """Endpoint protegido de teste"""
    return {"message": "Protected test endpoint"} 