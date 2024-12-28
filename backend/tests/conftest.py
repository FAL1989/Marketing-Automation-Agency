import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.app.database.connection import Base
from backend.app.core.config import settings
import redis.asyncio as redis
from unittest.mock import AsyncMock, MagicMock, patch
import pytest_asyncio
from prometheus_client import REGISTRY
from backend.app.core.monitoring import REGISTRY as app_registry

# Configuração do banco de dados de teste
engine = create_engine(settings.DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Mock OpenAI client
mock_openai = MagicMock()
mock_openai.chat.completions.create.return_value = MagicMock(
    choices=[MagicMock(message=MagicMock(content="Mocked response"))]
)

# Patch OpenAI before any imports
patch.dict('sys.modules', {'openai': mock_openai}).start()

# Now it's safe to import app-related modules
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Configura o banco de dados para os testes"""
    # Exclui todas as tabelas usando CASCADE
    with engine.connect() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
        connection.commit()
    
    # Cria todas as tabelas
    Base.metadata.create_all(bind=engine)
    yield
    
    # Exclui todas as tabelas usando CASCADE
    with engine.connect() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
        connection.commit()

@pytest.fixture(autouse=True)
def cleanup_database(db_session):
    """Limpa o banco de dados após cada teste"""
    yield
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(text(f"DELETE FROM {table.name}"))
    db_session.commit()

@pytest.fixture
def db_session():
    """Fornece uma sessão do banco de dados para os testes"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest_asyncio.fixture
async def mock_redis():
    """Mock do cliente Redis para testes"""
    mock = AsyncMock(spec=redis.Redis)
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = True
    return mock 

@pytest.fixture(autouse=True)
def clear_metrics():
    """Limpa as métricas entre os testes"""
    for collector in list(app_registry._collector_to_names.keys()):
        app_registry.unregister(collector)
    yield
    for collector in list(app_registry._collector_to_names.keys()):
        app_registry.unregister(collector) 

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def mock_redis():
    mock = MagicMock()
    mock.exists.return_value = False
    mock.incr.return_value = 1
    mock.expire.return_value = True
    mock.set.return_value = True
    return mock 