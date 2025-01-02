from sqlalchemy import create_engine
from ...app.db.base_class import Base
from ...app.db.base_all import *

def create_tables():
    """Cria todas as tabelas no banco de teste"""
    engine = create_engine("postgresql://aiagency:aiagency123@localhost:5432/aiagency_test")
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    create_tables() 