from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from ..models.generation import Generation
from ..models.user import User
from ..schemas.generation import GenerationCreate, GenerationResponse
from ..db.session import AsyncSessionLocal
from ..core.security import get_password_hash
from ..core.exceptions import NotFoundException

class GenerationService:
    """
    Serviço para gerenciar gerações de conteúdo
    """
    
    async def create_generation(
        self,
        generation: GenerationCreate,
        current_user: User
    ) -> Generation:
        """
        Cria uma nova geração de conteúdo
        """
        async with AsyncSessionLocal() as session:
            db_generation = Generation(
                user_id=current_user.id,
                prompt=generation.prompt,
                model=generation.model,
                parameters=generation.parameters,
                context=generation.context,
                status="pending"
            )
            session.add(db_generation)
            await session.commit()
            await session.refresh(db_generation)
            return db_generation

    async def list_generations(
        self,
        current_user: User
    ) -> List[Generation]:
        """
        Lista todas as gerações do usuário atual
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Generation)
                .where(Generation.user_id == current_user.id)
                .order_by(desc(Generation.created_at))
            )
            return result.scalars().all()

    async def get_generation(
        self,
        generation_id: int,
        current_user: User
    ) -> Optional[Generation]:
        """
        Obtém uma geração específica
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Generation)
                .where(
                    Generation.id == generation_id,
                    Generation.user_id == current_user.id
                )
            )
            return result.scalar_one_or_none() 