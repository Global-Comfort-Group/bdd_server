from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    DateTime, 
    Float, 
    ForeignKey, 
    Integer, 
    Numeric, 
    String, 
    Text,
    Enum as SQLEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import PropertyStatus, PropertyType


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lot_area: Mapped[float] = mapped_column(Float, nullable=False)
    property_type: Mapped[PropertyType] = mapped_column(SQLEnum(PropertyType), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="PHP", nullable=False)
    zoning_classification: Mapped[str] = mapped_column(String(100), nullable=False)
    title_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status and workflow
    status: Mapped[PropertyStatus] = mapped_column(
        SQLEnum(PropertyStatus), 
        nullable=False, 
        default="PROPERTY_SOURCING"
    )

    # Metadata
    submitted_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    reviewer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    submitted_by: Mapped["User"] = relationship(
        "User", 
        back_populates="submitted_properties",
        foreign_keys=[submitted_by_id]
    )
    reviewer: Mapped[Optional["User"]] = relationship(
        "User", 
        back_populates="reviewed_properties",
        foreign_keys=[reviewer_id]
    )
    attachments: Mapped[List["PropertyAttachment"]] = relationship(
        "PropertyAttachment", 
        back_populates="property",
        cascade="all, delete-orphan"
    )
    workflow_history: Mapped[List["WorkflowHistory"]] = relationship(
        "WorkflowHistory", 
        back_populates="property",
        cascade="all, delete-orphan"
    )


class PropertyAttachment(Base):
    __tablename__ = "property_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(Integer, ForeignKey("properties.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    cloudinary_public_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    cloudinary_url: Mapped[str] = mapped_column(String(500), nullable=False)
    cloudinary_secure_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # For images
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # For images
    uploaded_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    property: Mapped["Property"] = relationship("Property", back_populates="attachments")
    uploaded_by: Mapped["User"] = relationship("User")