from typing import Any, Dict, List, Optional, Type, TypeVar
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")

class BaseRepository:
    """
    Repositório base
    """
    def __init__(
        self,
        session: AsyncSession,
        model: Type[T]
    ):
        self.session = session
        self.model = model
        
    async def get_by_id(self, id: Any) -> Optional[T]:
        """
        Obtém registro por ID
        """
        query = select(self.model).where(self.model.id == id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
        
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None
    ) -> List[T]:
        """
        Obtém todos os registros com paginação
        """
        query = select(self.model)
        
        if order_by:
            if order_by.startswith("-"):
                column = getattr(self.model, order_by[1:])
                query = query.order_by(column.desc())
            else:
                column = getattr(self.model, order_by)
                query = query.order_by(column)
                
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
        
    async def get_by_filter(
        self,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100
    ) -> List[T]:
        """
        Obtém registros por filtros
        """
        query = select(self.model)
        
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)
                
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
        
    async def create(self, data: Dict[str, Any]) -> T:
        """
        Cria novo registro
        """
        obj = self.model(**data)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
        
    async def update(self, id: Any, data: Dict[str, Any]) -> Optional[T]:
        """
        Atualiza registro existente
        """
        obj = await self.get_by_id(id)
        if not obj:
            return None
            
        for field, value in data.items():
            if hasattr(obj, field):
                setattr(obj, field, value)
                
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
        
    async def delete(self, id: Any) -> bool:
        """
        Remove registro existente
        """
        obj = await self.get_by_id(id)
        if not obj:
            return False
            
        await self.session.delete(obj)
        await self.session.commit()
        return True
        
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Conta total de registros
        """
        query = select(func.count()).select_from(self.model)
        
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
                    
        result = await self.session.execute(query)
        return result.scalar_one() 