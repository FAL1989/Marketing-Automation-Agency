from sqlalchemy import create_engine, text
from app.db.base_class import Base
from app.db.base_all import *

def create_tables():
    """Cria todas as tabelas no banco de teste"""
    engine = create_engine("postgresql://aiagency:aiagency123@localhost:5432/aiagency_test")
    
    # Dropa todas as tabelas existentes
    Base.metadata.drop_all(bind=engine)
    
    # Cria todas as tabelas
    Base.metadata.create_all(bind=engine)
    
    print("Tabelas criadas com sucesso!")

if __name__ == "__main__":
    create_tables() 