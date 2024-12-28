from typing import Optional
from pydantic import BaseModel, EmailStr, Field, constr
from datetime import datetime

class UserBase(BaseModel):
    """Schema base para usuário."""
    username: constr(min_length=3, max_length=50) = Field(..., description="Nome de usuário")
    email: EmailStr = Field(..., description="Email do usuário")
    full_name: Optional[str] = Field(None, description="Nome completo do usuário")
    is_active: bool = Field(default=True, description="Se o usuário está ativo")
    is_superuser: bool = Field(default=False, description="Se o usuário é superusuário")

class UserCreate(UserBase):
    """Schema para criação de usuário."""
    password: constr(min_length=8) = Field(..., description="Senha do usuário")

class UserUpdate(BaseModel):
    """Schema para atualização de usuário."""
    email: Optional[EmailStr] = Field(None, description="Email do usuário")
    full_name: Optional[str] = Field(None, description="Nome completo do usuário")
    password: Optional[constr(min_length=8)] = Field(None, description="Senha do usuário")
    is_active: Optional[bool] = Field(None, description="Se o usuário está ativo")
    is_superuser: Optional[bool] = Field(None, description="Se o usuário é superusuário")

class User(UserBase):
    """Schema para resposta de usuário."""
    id: int = Field(..., description="ID do usuário")
    created_at: datetime = Field(..., description="Data de criação")
    updated_at: Optional[datetime] = Field(None, description="Data de atualização")

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: list[str] = []