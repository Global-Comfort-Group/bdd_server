from datetime import datetime
from enum import Enum
from typing import List

from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy import Boolean, DateTime, Integer, String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.enums import UserRole


class User(SQLAlchemyBaseUserTable[int]):
    __tablename__ = "user"

    # FastAPI-Users provides: id, email, hashed_password, is_active, is_superuser, is_verified
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False, default=UserRole.AGENT)
    company: Mapped[str] = mapped_column(String(100), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
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
    workflow_changes: Mapped[List["WorkflowHistory"]] = relationship(
        "WorkflowHistory", 
        back_populates="changed_by"
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"