from datetime import datetime
from typing import List

from sqlalchemy import Boolean, DateTime, Integer, String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import UserRole, AccountStatus


class User(Base):
    __tablename__ = "user"

    # Core user fields (matching FastAPI-Users structure)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(1024), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # BDD-specific fields
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    middle_name: Mapped[str] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False, default=UserRole.AGENT)
    company: Mapped[str] = mapped_column(String(100), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    avatar_url: Mapped[str] = mapped_column(String(500), nullable=True)  # Cloudinary URL for avatar
    account_status: Mapped[AccountStatus] = mapped_column(SQLEnum(AccountStatus), nullable=False, default=AccountStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    submitted_properties: Mapped[List["Property"]] = relationship(
        "Property", 
        back_populates="submitted_by", 
        foreign_keys="Property.submitted_by_id"
    )
    reviewed_properties: Mapped[List["Property"]] = relationship(
        "Property", 
        back_populates="reviewer", 
        foreign_keys="Property.reviewer_id"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    workflow_changes: Mapped[List["WorkflowHistory"]] = relationship(
        "WorkflowHistory", 
        back_populates="changed_by"
    )
    activity_logs: Mapped[List["ActivityLog"]] = relationship(
        "ActivityLog",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"