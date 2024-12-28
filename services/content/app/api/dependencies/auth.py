from typing import Dict, Any
import httpx
from fastapi import Depends, HTTPException, Header
from app.core.config import settings

async def get_current_user(
    authorization: str = Header(..., description="Token JWT no formato 'Bearer {token}'")
) -> Dict[str, Any]:
    """
    Valida o token JWT e retorna informações do usuário atual
    """
    try:
        # Verificar formato do token
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Token inválido: formato incorreto"
            )
        
        token = authorization.split(" ")[1]
        
        # Validar token com auth-service
        async with httpx.AsyncClient(timeout=settings.AUTH_SERVICE_TIMEOUT) as client:
            response = await client.get(
                f"{settings.AUTH_SERVICE_URL}/api/v1/auth/validate",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            # Verificar resposta
            response.raise_for_status()
            user_data = response.json()
            
            return user_data
            
    except httpx.HTTPError as e:
        if e.response and e.response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="Token inválido ou expirado"
            )
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao comunicar com auth-service: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno de autenticação: {str(e)}"
        ) 