from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from .session import AsyncSessionLocal

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Função assíncrona para obter uma sessão do banco de dados
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close() 