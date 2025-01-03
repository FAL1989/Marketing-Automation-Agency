from app.db.session import engine
from app.db.base_all import Base

async def create_tables():
    """
    Cria todas as tabelas do banco de dados
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    import asyncio
    asyncio.run(create_tables()) 