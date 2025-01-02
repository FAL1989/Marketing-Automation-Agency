"""
Configurações e fixtures para testes
"""

import os
import sys
from pathlib import Path

# Configura as variáveis de ambiente para teste
os.environ["TESTING"] = "true"
os.environ["POSTGRES_SERVER"] = "localhost"
os.environ["POSTGRES_USER"] = "postgres"
os.environ["POSTGRES_PASSWORD"] = "postgres"
os.environ["POSTGRES_DB"] = "app_test"
os.environ["POSTGRES_PORT"] = "5432"
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6379"
os.environ["REDIS_DB"] = "1"
os.environ["REDIS_RATELIMIT_DB"] = "2"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["SECRET_KEY"] = "test-secret-key-very-very-secure"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-very-very-secure"
os.environ["JWT_REFRESH_SECRET_KEY"] = "test-jwt-refresh-secret-key-very-very-secure"
os.environ["USE_SQLITE"] = "true"  # Força o uso do SQLite para testes
os.environ["RATE_LIMIT_PER_MINUTE"] = "60"  # Convertido para int nas configurações
os.environ["RATE_LIMIT_PER_SECOND"] = "1"  # Convertido para int nas configurações
os.environ["RATE_LIMIT_PERIOD"] = "60"  # Convertido para int nas configurações
os.environ["RATE_LIMIT_MAX_REQUESTS"] = "100"  # Convertido para int nas configurações
os.environ["RATE_LIMIT_BURST"] = "5"  # Convertido para int nas configurações

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import logging

# Adiciona o diretório raiz ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.core.config import Settings
from app.db.base import Base
from app.main import app
from app.db.session import get_db
from app.models.user import User
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)

# Configurações de teste
test_settings = Settings(
    TESTING=True,
    # Database (SQLite para testes)
    USE_SQLITE=True,
    SQLALCHEMY_DATABASE_URI="sqlite+aiosqlite:///./test.db",
    
    # Pool settings
    SQLALCHEMY_POOL_SIZE=5,
    SQLALCHEMY_MAX_OVERFLOW=10,
    SQLALCHEMY_POOL_TIMEOUT=30,
    
    # Redis
    REDIS_HOST="localhost",
    REDIS_PORT=6379,
    REDIS_DB=1,
    REDIS_RATELIMIT_DB=2,
    # A URL será construída automaticamente pelo validator
    
    # Security
    SECRET_KEY="test-secret-key-very-very-secure",
    JWT_SECRET_KEY="test-jwt-secret-key-very-very-secure",
    JWT_REFRESH_SECRET_KEY="test-jwt-refresh-secret-key-very-very-secure",
    ACCESS_TOKEN_EXPIRE_MINUTES=15,
    REFRESH_TOKEN_EXPIRE_MINUTES=60 * 24 * 7,  # 7 days
    
    # Rate Limiting
    RATE_LIMIT_ENABLED=True,
    RATE_LIMIT_MAX_REQUESTS=100,
    RATE_LIMIT_PERIOD=60,  # 60 segundos
    RATE_LIMIT_PER_MINUTE=60,  # 60 requisições por minuto
    RATE_LIMIT_PER_SECOND=1,  # 1 requisição por segundo
    RATE_LIMIT_BURST=5,
    RATE_LIMIT_EXCLUDE_PATHS=["/api/v1/health", "/metrics"],
    
    # Frontend
    FRONTEND_URL="http://localhost:3000",
    
    # Metrics
    METRICS_PORT=9090,
    
    # Debug
    DEBUG=True,

    # SMTP Settings (desabilitado para testes)
    SMTP_HOST="",
    SMTP_PORT=587,
    SMTP_USER="",
    SMTP_PASSWORD="",
    SMTP_FROM_EMAIL="test@example.com",
    SMTP_TLS=True,
    SMTP_SSL=False,
    SMTP_USE_CREDENTIALS=False,
    SMTP_VALIDATE_CERTS=True,

    # Slack Settings (desabilitado para testes)
    SLACK_WEBHOOK_URL="",
    SLACK_CHANNEL="#test-monitoring",
    SLACK_USERNAME="AI Agency Test Bot",
    SLACK_ICON_EMOJI=":test:",
    SLACK_ENABLED=False,

    # Circuit Breaker Settings
    CIRCUIT_BREAKER_FAILURE_THRESHOLD=3,  # Menor para testes
    CIRCUIT_BREAKER_RESET_TIMEOUT=30,  # Menor para testes
    CIRCUIT_BREAKER_MAX_FAILURES=2,  # Menor para testes
    CIRCUIT_BREAKER_RETRY_TIME=15,  # Menor para testes
    CIRCUIT_BREAKER_EXCLUDE_PATHS=["/api/v1/health", "/metrics"],

    # API Key Settings
    API_KEY="test-api-key-very-very-secure"  # API key fixa para testes
)

# Engine de teste (SQLite)
engine = create_async_engine(
    str(test_settings.SQLALCHEMY_DATABASE_URI),
    **test_settings.SQLALCHEMY_ENGINE_OPTIONS
)

# Sessão de teste
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Cria um event loop para os testes"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Configura o banco de dados de teste"""
    try:
        # Remove o arquivo do banco de dados se existir
        db_file = Path("./test.db")
        if db_file.exists():
            db_file.unlink()
            
        # Cria as tabelas
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("Banco de dados de teste configurado com sucesso")
        yield
        
    except Exception as e:
        logger.error(f"Erro ao configurar banco de dados de teste: {e}")
        raise
    finally:
        # Limpa o banco de dados após os testes
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("Banco de dados de teste limpo com sucesso")
        except Exception as e:
            logger.error(f"Erro ao limpar banco de dados de teste: {e}")

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Fornece uma sessão de banco de dados para os testes"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.rollback()
            # Limpa todas as tabelas após cada teste
            for table in reversed(Base.metadata.sorted_tables):
                await session.execute(f'DELETE FROM {table.name}')
            await session.commit()

@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[TestClient, None]:
    """Fornece um cliente de teste"""
    async def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
async def test_user(db_session: AsyncSession) -> AsyncGenerator[User, None]:
    """
    Fixture que cria um usuário de teste.
    Importante para testes de autenticação e autorização.
    """
    try:
        logger.info("Criando usuário de teste")
        
        # Cria um novo usuário
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("testpass123"),
            full_name="Test User",
            is_active=True,
            is_superuser=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_login=datetime.utcnow(),
            mfa_enabled=False,
            mfa_secret=None,
            failed_login_attempts=0,
            lockout_until=None
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        logger.info(f"Usuário de teste criado com ID: {user.id}")
        
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

@pytest.fixture(autouse=True)
def test_env():
    """Configura as variáveis de ambiente para teste"""
    # As variáveis já foram configuradas no início do arquivo
    yield 