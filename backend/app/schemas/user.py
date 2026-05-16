"""
Schémas Pydantic pour les utilisateurs.
"""

from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=100)
    email: EmailStr | None = None


class UserInDB(UserBase):
    id: UUID
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserResponse(UserInDB):
    pass