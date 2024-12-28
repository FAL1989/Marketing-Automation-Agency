from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ..core.config import settings

# Cria o engine do SQLAlchemy
engine = create_engine(settings.DATABASE_URL)

# Cria a classe base para os modelos
Base = declarative_base()

# Cria a fábrica de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Inicializa o banco de dados"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Fornece uma sessão do banco de dados"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 