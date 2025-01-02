from sqlalchemy import create_engine
from app.db.base_class import Base
from app.models.user import User
from app.models.audit import AuditLog
from app.models.content import Content
from app.models.template import Template

# URL do banco de dados de teste
SQLALCHEMY_DATABASE_URL = "postgresql://aiagency:aiagency123@localhost:5432/aiagency_test"

def create_tables():
    # Criar engine
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    # Criar todas as tabelas
    Base.metadata.create_all(bind=engine)
    
    print("Tabelas criadas com sucesso!")

if __name__ == "__main__":
    create_tables() 