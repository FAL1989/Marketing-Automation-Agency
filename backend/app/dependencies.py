from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, AsyncGenerator, Generator
import redis.asyncio as redis
from .core.config import settings
import structlog
from cachetools import TTLCache
import json
import aiohttp
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

from .database.session import get_db
from .models.user import User
from .core.security import verify_password
from .services.ai_service import AIService
from .services.ai_config_service import AIConfigService
from .services.queue_service import QueueService
from .services.rate_limiter import TokenBucketRateLimiter
from .services.monitoring_service import MonitoringService

logger = structlog.get_logger()

# Configuração do OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Cache de tokens com TTL de 30 minutos e limite de 2000 itens
token_cache = TTLCache(maxsize=2000, ttl=1800)

# Cache de usuários com TTL de 5 minutos
user_cache = TTLCache(maxsize=1000, ttl=300)

# Inicialização do cliente Redis
_redis_client = None

async def get_redis_client() -> AsyncGenerator[redis.Redis, None]:
    """Fornece um cliente Redis com retry e fallback"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
            max_connections=20
        )
    try:
        # Verifica a conexão com retry
        await _redis_client.ping()
        yield _redis_client
    except redis.ConnectionError as e:
        logger.error("Erro de conexão com Redis", error=str(e))
        # Fallback para cache local se Redis não estiver disponível
        yield None
    finally:
        if _redis_client:
            await _redis_client.close()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    # Armazena o token no cache local
    token_cache[encoded_jwt] = {
        "user": to_encode.get("sub"),
        "exp": expire.timestamp()
    }
    
    return encoded_jwt

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verifica cache local primeiro
        cached_token = token_cache.get(token)
        if cached_token:
            username = cached_token["user"]
            if datetime.fromtimestamp(cached_token["exp"]) > datetime.utcnow():
                # Verifica cache de usuário
                cached_user = user_cache.get(username)
                if cached_user:
                    return cached_user
                
                # Se não estiver no cache de usuário, busca do banco
                user = db.query(User).filter(User.email == username).first()
                if user:
                    user_cache[username] = user
                    return user
        
        # Se não estiver no cache local, verifica Redis
        if redis_client:
            blacklisted = await redis_client.exists(f"blacklist:{token}")
            if blacklisted:
                raise credentials_exception
            
            cached_user_data = await redis_client.get(f"user:{token}")
            if cached_user_data:
                user_data = json.loads(cached_user_data)
                user = db.query(User).filter(User.email == user_data["username"]).first()
                if user:
                    # Atualiza caches
                    token_cache[token] = {
                        "user": user.email,
                        "exp": user_data["exp"]
                    }
                    user_cache[user.email] = user
                    return user
        
        # Se não encontrou nos caches, decodifica o token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
            
        # Busca usuário do banco
        user = db.query(User).filter(User.email == username).first()
        if user is None:
            raise credentials_exception
            
        # Atualiza caches
        token_cache[token] = {
            "user": username,
            "exp": payload["exp"]
        }
        user_cache[username] = user
        
        # Atualiza Redis se disponível
        if redis_client:
            await redis_client.setex(
                f"user:{token}",
                settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                json.dumps({
                    "username": username,
                    "exp": payload["exp"]
                })
            )
        
        return user
            
    except (JWTError, Exception) as e:
        logger.error("Erro na autenticação", error=str(e))
        raise credentials_exception

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    return current_user

async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user

async def get_monitoring_service() -> AsyncGenerator[MonitoringService, None]:
    """Provê o serviço de monitoramento"""
    service = MonitoringService()
    try:
        yield service
    finally:
        await service.close()

async def get_config_service() -> AsyncGenerator[AIConfigService, None]:
    """Provê o serviço de configuração"""
    service = AIConfigService()
    try:
        yield service
    finally:
        await service.close()

async def get_queue_service(
    monitoring: MonitoringService = Depends(get_monitoring_service)
) -> AsyncGenerator[QueueService, None]:
    """Provê o serviço de filas"""
    service = QueueService(settings.REDIS_URL, monitoring)
    try:
        yield service
    finally:
        await service.close()

async def get_rate_limiter() -> AsyncGenerator[TokenBucketRateLimiter, None]:
    """Provê o serviço de rate limiting"""
    service = TokenBucketRateLimiter(settings.REDIS_URL)
    try:
        yield service
    finally:
        await service.close()

async def get_ai_service(
    config: AIConfigService = Depends(get_config_service),
    queue: QueueService = Depends(get_queue_service),
    rate_limiter: TokenBucketRateLimiter = Depends(get_rate_limiter),
    monitoring: MonitoringService = Depends(get_monitoring_service)
) -> AsyncGenerator[AIService, None]:
    """Provê o serviço de IA"""
    service = AIService(config, queue, rate_limiter, monitoring)
    try:
        yield service
    finally:
        await service.close() 