from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_serializer

from app.models.enums import UserRole, AccountStatus


# Safe user schema without any sensitive fields
class UserPublic(BaseModel):
    """Public user data - no sensitive information"""
    id: int
    email: EmailStr
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    role: UserRole
    company: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool = True
    account_status: AccountStatus
    created_at: datetime
    updated_at: datetime
    
    @field_serializer('avatar_url')
    def _sign_avatar_url(self, value: Optional[str]) -> Optional[str]:
        """Stored avatar URLs point at a private bucket; sign them on the way out."""
        from app.services.oss_service import resign_stored_url
        return resign_stored_url(value)

    @property
    def full_name(self) -> str:
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    class Config:
        from_attributes = True


class UserRead(BaseModel):
    """User schema for read operations"""
    id: int
    email: EmailStr
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    role: UserRole
    company: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    account_status: AccountStatus
    created_at: datetime
    updated_at: datetime

    @field_serializer('avatar_url')
    def _sign_avatar_url(self, value: Optional[str]) -> Optional[str]:
        """Stored avatar URLs point at a private bucket; sign them on the way out."""
        from app.services.oss_service import resign_stored_url
        return resign_stored_url(value)

    @property
    def full_name(self) -> str:
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """User schema for creation"""
    email: EmailStr
    password: str
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    role: UserRole = UserRole.AGENT
    company: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False
    account_status: Optional[AccountStatus] = AccountStatus.PENDING


class UserUpdate(BaseModel):
    """User schema for updates"""
    password: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    is_verified: Optional[bool] = None
    account_status: Optional[AccountStatus] = None


class UserListResponse(BaseModel):
    """Response model for paginated user list"""
    users: List[UserRead]
    total: int
    skip: int
    limit: int
    
    class Config:
        from_attributes = True