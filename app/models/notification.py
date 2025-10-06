from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class NotificationType(str, Enum):
    """Notification types"""
    DUPLICATE_DETECTED = "DUPLICATE_DETECTED"
    PROPERTY_APPROVED = "PROPERTY_APPROVED"
    PROPERTY_REJECTED = "PROPERTY_REJECTED"
    PROPERTY_ASSIGNED = "PROPERTY_ASSIGNED"
    PROPERTY_MERGED = "PROPERTY_MERGED"
    SYSTEM_ALERT = "SYSTEM_ALERT"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    notification_type: Mapped[NotificationType] = mapped_column(
        SQLEnum(NotificationType), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Link to related property (optional)
    property_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("properties.id"), nullable=True
    )
    
    # Link to duplicate property (if applicable)
    duplicate_property_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("properties.id"), nullable=True
    )
    
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")
    property: Mapped[Optional["Property"]] = relationship(
        "Property", foreign_keys=[property_id], back_populates="notifications"
    )
    duplicate_property: Mapped[Optional["Property"]] = relationship(
        "Property", foreign_keys=[duplicate_property_id]
    )

