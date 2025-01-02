from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .core.config import settings
from .core.security import verify_token
from .db.session import AsyncSessionLocal
from .models.user import User
from .schemas.auth import TokenPayload
from .core.circuit_breaker import CircuitBreaker, CircuitState
from sqlalchemy.sql import text
from .db.base_class import Base
from .core.mfa import MFAService
import logging

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

# Cria o circuit breaker
auth_circuit_breaker = CircuitBreaker(
    service_name="auth_service",
    failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
    reset_timeout=settings.CIRCUIT_BREAKER_RESET_TIMEOUT
)

async def get_db():
    """
    Dependency para obter uma sessão do banco de dados
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependency para obter o usuário atual a partir do token JWT
    """
    try:
        logger.info("Iniciando get_current_user")
        logger.debug(f"Token recebido: {token[:20]}...")
        
        # Verifica o token
        payload = verify_token(token)
        if not payload:
            logger.error("Token inválido")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Obtém o usuário
        stmt = select(User).where(User.email == payload.get("sub"))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            logger.error("Usuário não encontrado")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
            
        # Verifica se o usuário está ativo
        if not user.is_active:
            logger.error("Usuário inativo")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuário inativo"
            )
            
        logger.info(f"Usuário autenticado: {user.email}")
        return user
        
    except JWTError as e:
        logger.error(f"Erro ao decodificar token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error("Erro inesperado: %s", str(e))
        await auth_circuit_breaker.record_failure(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

async def verify_mfa_enabled(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Verifica se o MFA está habilitado para o usuário
    """
    if not user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA não está habilitado para este usuário"
        )

async def verify_mfa_disabled(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Verifica se o MFA está desabilitado para o usuário
    """
    if user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA já está habilitado para este usuário"
        ) 