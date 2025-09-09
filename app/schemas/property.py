from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, validator

from app.models.enums import PropertyType, PropertyStatus
from app.schemas.user import UserRead
from app.schemas.workflow import WorkflowHistoryRead


class PropertyBase(BaseModel):
    name: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    lot_area: float
    property_type: PropertyType
    price: Decimal
    currency: str = "PHP"
    zoning_classification: str
    title_number: str
    description: Optional[str] = None


class PropertyCreate(PropertyBase):
    @validator('price')
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return v

    @validator('lot_area')
    def lot_area_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Lot area must be positive')
        return v


class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    lot_area: Optional[float] = None
    property_type: Optional[PropertyType] = None
    price: Optional[Decimal] = None
    currency: Optional[str] = None
    zoning_classification: Optional[str] = None
    title_number: Optional[str] = None
    description: Optional[str] = None
    reviewer_id: Optional[int] = None

    @validator('price')
    def price_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Price must be positive')
        return v

    @validator('lot_area')
    def lot_area_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Lot area must be positive')
        return v


class PropertyRead(PropertyBase):
    id: int
    status: PropertyStatus
    submitted_by_id: int
    reviewer_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    # Related objects
    submitted_by: Optional[UserRead] = None
    reviewer: Optional[UserRead] = None
    attachments: List["PropertyAttachmentRead"] = []
    workflow_history: List[WorkflowHistoryRead] = []

    class Config:
        from_attributes = True


class PropertyListRead(BaseModel):
    id: int
    name: str
    address: str
    property_type: PropertyType
    price: Decimal
    currency: str
    status: PropertyStatus
    created_at: datetime
    submitted_by: Optional[UserRead] = None

    class Config:
        from_attributes = True


# Property Attachment Schemas
class PropertyAttachmentBase(BaseModel):
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    width: Optional[int] = None  # For images
    height: Optional[int] = None  # For images


class PropertyAttachmentCreate(PropertyAttachmentBase):
    property_id: int
    cloudinary_public_id: str
    cloudinary_url: str
    cloudinary_secure_url: str


class PropertyAttachmentRead(PropertyAttachmentBase):
    id: int
    property_id: int
    cloudinary_public_id: str
    cloudinary_url: str
    cloudinary_secure_url: str
    uploaded_by_id: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


# Update PropertyRead to resolve forward reference
PropertyRead.model_rebuild()