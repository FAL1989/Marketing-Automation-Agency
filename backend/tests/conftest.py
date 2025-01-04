"""
Configurações e fixtures para testes
"""

import os
import sys
from pathlib import Path
import pyotp
from datetime import datetime, timedelta, UTC
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator, Generator, Any, Dict
from fastapi.testclient import TestClient
import pytest
import pytest_asyncio
import asyncio
import logging
from redis import Redis

# Adiciona o diretório raiz ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.core.config import Settings
from app.db.base import Base
from app.main import app
from app.db.session import get_db
from app.models.user import User
from app.models.audit import AuditLog
from app.models.content import Content
from app.models.template import Template
from app.models.generation import Generation
from app.core.security import get_password_hash
from app.services.monitoring_service import MonitoringService
from app.services.rate_limiter import TokenBucketRateLimiter
from app.core.config import settings
from app.core.redis import RedisManager, get_redis_client

# Configura as variáveis de ambiente para teste
os.environ["TESTING"] = "true"
os.environ["USE_SQLITE"] = "true"  # Força o uso do SQLite para testes
os.environ["RATE_LIMIT_PER_MINUTE"] = "60"
os.environ["RATE_LIMIT_PER_SECOND"] = "1"
os.environ["RATE_LIMIT_PERIOD"] = "60"
os.environ["RATE_LIMIT_MAX_REQUESTS"] = "100"
os.environ["RATE_LIMIT_BURST"] = "5"
os.environ["SECRET_KEY"] = "test-secret-key-very-very-secure"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-very-very-secure"
os.environ["JWT_REFRESH_SECRET_KEY"] = "test-jwt-refresh-secret-key-very-very-secure"

logger = logging.getLogger(__name__)

# Configurações de teste
test_settings = Settings(
    TESTING=True,
    USE_SQLITE=True,
    SQLALCHEMY_DATABASE_URI="sqlite+aiosqlite:///./test.db",
    DEBUG=True,
)

# Engine de teste (SQLite)
engine = create_async_engine(
    test_settings.SQLALCHEMY_DATABASE_URI,
    connect_args={"check_same_thread": False},
    echo=True
)

# Sessão de teste
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

@pytest_asyncio.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create a single event loop for all async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create a test database engine."""
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        # Start a nested transaction
        async with session.begin():
            # Use a savepoint to be able to rollback to it
            await session.begin_nested()
            try:
                yield session
            finally:
                # Always rollback the nested transaction
                await session.rollback()
                # Close the session
                await session.close()

@pytest_asyncio.fixture
async def redis() -> AsyncGenerator[Redis, None]:
    """Create a test Redis connection."""
    redis_manager = RedisManager()
    await redis_manager.initialize()
    redis_client = await redis_manager.get_redis()
    try:
        yield redis_client
    finally:
        await redis_manager.close()

@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)

@pytest.fixture
async def test_user(db_session: AsyncSession) -> AsyncGenerator[User, None]:
    """
    Fixture que cria um usuário de teste.
    Importante para testes de autenticação e autorização.
    """
    try:
        logger.info("Criando usuário de teste")
        
        # Cria um novo usuário sem MFA
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("test123"),
            full_name="Test User",
            is_active=True,
            is_superuser=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_login=datetime.now(UTC),
            mfa_enabled=False,
            mfa_secret=None,
            mfa_backup_codes=None,
            mfa_attempts=0,
            mfa_locked_until=None,
            mfa_last_used=None
        )
        
        db_session.add(user)
        await db_session.flush()  # Flush to get the ID but don't commit yet
        await db_session.refresh(user)
        
        yield user
        
    except Exception as e:
        logger.error(f"Erro ao criar usuário de teste: {e}")
        raise
    finally:
        try:
            await db_session.delete(user)
            await db_session.commit()
            logger.info("Usuário de teste removido")
        except Exception as e:
            logger.error(f"Erro ao remover usuário de teste: {e}")

@pytest.fixture
def monitoring() -> MonitoringService:
    """Fornece uma instância limpa do MonitoringService"""
    service = MonitoringService()
    return service 