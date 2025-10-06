from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class ActivityAction(str, enum.Enum):
    """Activity action types"""
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    ACTIVATE = "ACTIVATE"
    DEACTIVATE = "DEACTIVATE"
    ROLE_CHANGE = "ROLE_CHANGE"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    EXPORT = "EXPORT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    STATUS_CHANGE = "STATUS_CHANGE"


class ResourceType(str, enum.Enum):
    """Resource types for activity tracking"""
    USER = "USER"
    PROPERTY = "PROPERTY"
    NEGO_TABLE = "NEGO_TABLE"
    NEGOTIATION_CHRONICLE = "NEGOTIATION_CHRONICLE"
    SYSTEM = "SYSTEM"
    DUPLICATE = "DUPLICATE"
    NOTIFICATION = "NOTIFICATION"


class ActivityLog(Base):
    """Activity log model for tracking user actions"""
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(SQLEnum(ActivityAction), nullable=False, index=True)
    resource_type = Column(SQLEnum(ResourceType), nullable=False, index=True)
    resource_id = Column(Integer, nullable=True, index=True)
    details = Column(Text, nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv6 can be up to 45 chars
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationship
    user = relationship("User", back_populates="activity_logs")

    def __repr__(self):
        return f"<ActivityLog(id={self.id}, user_id={self.user_id}, action={self.action}, resource={self.resource_type})>"

