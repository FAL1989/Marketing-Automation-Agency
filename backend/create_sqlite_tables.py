import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.db.base_class import Base
from app.db.base_all import *
from app.core.config import settings

async def create_tables():
    """Cria todas as tabelas no banco SQLite"""
    engine = create_async_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=settings.SQL_DEBUG
    )
    
    async with engine.begin() as conn:
        # Dropa todas as tabelas existentes
        await conn.run_sync(Base.metadata.drop_all)
        
        # Cria todas as tabelas
        await conn.run_sync(Base.metadata.create_all)
    
    print("Tabelas criadas com sucesso!")

if __name__ == "__main__":
    asyncio.run(create_tables()) 