from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Boolean,
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
from app.models.enums import PropertyStatus, PropertyType, TransactionStatus


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Google Places API data
    place_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Detailed address components (Google Places format)
    street: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    barangay_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    province_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    region_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="Philippines")
    lot_area: Mapped[float] = mapped_column(Float, nullable=False)
    property_type: Mapped[PropertyType] = mapped_column(SQLEnum(PropertyType), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)  # Sale price or primary price
    lease_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)  # Lease price for SL transactions
    building_area: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    floors: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    parking_slots: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rooms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="PHP", nullable=False)
    zoning_classification: Mapped[str] = mapped_column(String(100), nullable=False)
    title_number: Mapped[Optional[str]] = mapped_column(String(100), unique=False, nullable=True, index=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    referred_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # Name or company that referred this property

    # Status and workflow
    status: Mapped[PropertyStatus] = mapped_column(
        SQLEnum(PropertyStatus), 
        nullable=False, 
        default="PROPERTY_SOURCING"
    )
    transaction_status: Mapped[TransactionStatus] = mapped_column(
        SQLEnum(TransactionStatus),
        nullable=False,
        default="S"  # Default to SALE
    )

    # Metadata
    submitted_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    reviewer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Duplicate tracking
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    duplicate_of_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("properties.id"), nullable=True)
    duplicate_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Mark/Bookmark for review
    is_marked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Bookmark flag for quick access/review

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
    nego_tables: Mapped[List["NegoTable"]] = relationship(
        "NegoTable", 
        back_populates="property",
        cascade="all, delete-orphan"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", 
        foreign_keys="Notification.property_id",
        back_populates="property",
        cascade="all, delete-orphan"
    )
    
    # Self-referential relationship for duplicates
    duplicate_of: Mapped[Optional["Property"]] = relationship(
        "Property",
        remote_side="Property.id",
        foreign_keys=[duplicate_of_id]
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
    document_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g. 'pby_ffs', 'due_diligence', or None for general
    uploaded_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    property: Mapped["Property"] = relationship("Property", back_populates="attachments")
    uploaded_by: Mapped["User"] = relationship("User")