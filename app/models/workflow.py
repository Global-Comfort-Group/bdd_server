from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import PropertyStatus


class WorkflowHistory(Base):
    __tablename__ = "workflow_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(Integer, ForeignKey("properties.id"), nullable=False)
    from_status: Mapped[Optional[PropertyStatus]] = mapped_column(SQLEnum(PropertyStatus), nullable=True)
    to_status: Mapped[PropertyStatus] = mapped_column(SQLEnum(PropertyStatus), nullable=False)
    changed_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    property: Mapped["Property"] = relationship("Property", back_populates="workflow_history")
    changed_by: Mapped["User"] = relationship("User", back_populates="workflow_changes")