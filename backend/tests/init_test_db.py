from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.models.user import User
from app.models.audit import AuditLog
from app.models.content import Content
from app.models.template import Template

# Criar engine de teste
SQLALCHEMY_DATABASE_URL = "postgresql://aiagency:aiagency123@localhost:5432/aiagency_test"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

def init_db():
    # Remover todas as tabelas existentes
    Base.metadata.drop_all(bind=engine)
    
    # Criar todas as tabelas
    Base.metadata.create_all(bind=engine)
    
    print("Banco de dados de teste inicializado com sucesso!")

if __name__ == "__main__":
    init_db() 