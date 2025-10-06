from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.models.notification import NotificationType


class NotificationBase(BaseModel):
    """Base notification schema"""
    notification_type: NotificationType
    title: str
    message: str
    property_id: Optional[int] = None
    duplicate_property_id: Optional[int] = None


class NotificationCreate(NotificationBase):
    """Schema for creating a notification"""
    user_id: int


class NotificationRead(NotificationBase):
    """Schema for reading a notification"""
    id: int
    user_id: int
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationUpdate(BaseModel):
    """Schema for updating a notification"""
    is_read: Optional[bool] = None

