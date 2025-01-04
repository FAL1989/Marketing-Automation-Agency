from typing import Any, Dict, Optional, Union, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

class CRUDUser:
    """CRUD para usuários"""
    
    async def get(self, db: AsyncSession, id: int) -> Optional[User]:
        """
        Obtém um usuário pelo ID.
        """
        result = await db.execute(select(User).filter(User.id == id))
        return result.scalar_one_or_none()
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """
        Obtém um usuário pelo email.
        """
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalar_one_or_none()
    
    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        Obtém múltiplos usuários.
        """
        result = await db.execute(select(User).offset(skip).limit(limit))
        return result.scalars().all()
    
    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """
        Cria um novo usuário.
        """
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            is_active=obj_in.is_active,
            is_superuser=obj_in.is_superuser
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: User,
        obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        """
        Atualiza um usuário.
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        
        stmt = (
            update(User)
            .where(User.id == db_obj.id)
            .values(**update_data)
            .returning(User)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.scalar_one()
    
    async def remove(self, db: AsyncSession, *, id: int) -> Optional[User]:
        """
        Remove um usuário.
        """
        stmt = delete(User).where(User.id == id).returning(User)
        result = await db.execute(stmt)
        await db.commit()
        return result.scalar_one_or_none()
    
    async def authenticate(
        self,
        db: AsyncSession,
        *,
        email: str,
        password: str
    ) -> Optional[User]:
        """
        Autentica um usuário.
        """
        user = await self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    async def is_active(self, user: User) -> bool:
        """
        Verifica se um usuário está ativo.
        """
        return user.is_active
    
    async def is_superuser(self, user: User) -> bool:
        """
        Verifica se um usuário é superusuário.
        """
        return user.is_superuser

user = CRUDUser() 