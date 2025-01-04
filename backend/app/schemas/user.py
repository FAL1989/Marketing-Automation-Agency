from typing import Optional, Annotated
from pydantic import BaseModel, EmailStr, Field, constr
from pydantic import ConfigDict

class User(BaseModel):
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    full_name: Optional[str] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: Annotated[str, Field(min_length=6, max_length=100)]
    full_name: Annotated[str, Field(min_length=1, max_length=100)]
    is_active: bool = True
    is_superuser: bool = False

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[Annotated[str, Field(min_length=1, max_length=100)]] = None
    password: Optional[Annotated[str, Field(min_length=6, max_length=100)]] = None

class UserInDB(User):
    hashed_password: str

class UserOut(User):
    model_config = ConfigDict(from_attributes=True)
    
    id: int