from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import verify_password, create_access_token
from app.dependencies import get_db
from app.models.user import User
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Endpoint de login"""
    try:
        logger.info("Tentativa de login", username=form_data.username)
        
        # Buscar usuário pelo email
        user = db.query(User).filter(User.email == form_data.username).first()
        
        # Se não encontrar pelo email, tenta pelo username
        if not user:
            user = db.query(User).filter(User.username == form_data.username).first()
        
        # Verificar se o usuário existe e a senha está correta
        if not user:
            logger.warning("Usuário não encontrado", username=form_data.username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        if not verify_password(form_data.password, user.hashed_password):
            logger.warning("Senha incorreta", username=form_data.username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Gerar token de acesso
        access_token = create_access_token(
            data={"sub": user.username}
        )
        
        logger.info("Login bem-sucedido", username=user.username)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.username
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro no processo de login", error=str(e), username=form_data.username)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e
    finally:
        db.close() 