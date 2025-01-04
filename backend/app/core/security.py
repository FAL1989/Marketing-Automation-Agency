"""
Módulo de segurança para autenticação e autorização
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from fastapi import HTTPException, Security, status, Depends
from ..core.config import settings
from app.schemas.user import User

# Configuração do contexto de criptografia
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuração do OAuth2
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    scheme_name="JWT"
)

# Configuração da API Key
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def verify_api_key(api_key: str = Security(api_key_header)) -> bool:
    """
    Verifica se a API key é válida.
    
    Args:
        api_key: API key a ser verificada
        
    Returns:
        True se a API key é válida
        
    Raises:
        HTTPException: Se a API key é inválida
    """
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate API key"
        )
    return True

def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Cria um token JWT de acesso.
    
    Args:
        subject: Identificador do usuário (geralmente email ou ID)
        expires_delta: Tempo de expiração do token
        
    Returns:
        Token JWT codificado
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Cria um token JWT de refresh.
    
    Args:
        subject: Identificador do usuário (geralmente email ou ID)
        expires_delta: Tempo de expiração do token
        
    Returns:
        Token JWT codificado
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se uma senha em texto plano corresponde ao hash armazenado.
    
    Args:
        plain_password: Senha em texto plano
        hashed_password: Hash da senha armazenado
        
    Returns:
        True se a senha corresponde ao hash, False caso contrário
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Gera um hash seguro para uma senha.
    
    Args:
        password: Senha em texto plano
        
    Returns:
        Hash da senha
    """
    return pwd_context.hash(password)

def verify_token(token: str, refresh: bool = False) -> Dict[str, Any]:
    """
    Verifica e decodifica um token JWT.
    
    Args:
        token: Token JWT a ser verificado
        refresh: Se True, verifica um token de refresh
        
    Returns:
        Payload do token decodificado
        
    Raises:
        JWTError: Se o token for inválido ou expirado
    """
    secret = settings.JWT_REFRESH_SECRET_KEY if refresh else settings.JWT_SECRET_KEY
    return jwt.decode(
        token, secret, algorithms=[settings.ALGORITHM]
    )

class SecurityService:
    """
    Serviço para operações de segurança
    """
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifica se uma senha em texto plano corresponde ao hash armazenado.
        """
        return self.pwd_context.verify(plain_password, hashed_password)
        
    def get_password_hash(self, password: str) -> str:
        """
        Gera um hash seguro para uma senha.
        """
        return self.pwd_context.hash(password)
        
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Cria um token JWT de acesso.
        """
        return create_access_token(data, expires_delta)
        
    def create_refresh_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Cria um token JWT de refresh.
        """
        return create_refresh_token(data, expires_delta)
        
    def verify_token(self, token: str, refresh: bool = False) -> Dict[str, Any]:
        """
        Verifica e decodifica um token JWT.
        """
        return verify_token(token, refresh)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Obtém o usuário atual a partir do token JWT
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Para testes, retorna um usuário mock
    user = User(
        email=email,
        is_active=True,
        is_superuser=False,
        full_name="Test User"
    )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário inativo"
        )
    
    return user

__all__ = [
    "create_access_token",
    "create_refresh_token",
    "verify_password",
    "get_password_hash",
    "verify_token",
    "SecurityService",
    "oauth2_scheme",
    "verify_api_key",
    "api_key_header"
] 