from datetime import datetime
from typing import Optional
from fastapi_users import schemas
from pydantic import EmailStr

from app.models.enums import UserRole


class UserRead(schemas.BaseUser[int]):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    company: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    class Config:
        from_attributes = True


class UserCreate(schemas.BaseUserCreate):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: UserRole = UserRole.AGENT
    company: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False


class UserUpdate(schemas.BaseUserUpdate):
    password: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    is_verified: Optional[bool] = None