from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, validator

from app.models.enums import PropertyType, PropertyStatus, TransactionStatus, ZoningClassification
from app.schemas.user import UserPublic
from app.schemas.workflow import WorkflowHistoryRead


class PropertyBase(BaseModel):
    name: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # Google Places API data
    place_id: Optional[str] = None
    
    # Detailed address components (Google Places format)
    street: Optional[str] = None
    barangay_name: Optional[str] = None
    city_name: Optional[str] = None
    province_name: Optional[str] = None
    region_name: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = "Philippines"
    
    lot_area: float
    property_type: PropertyType
    price: Decimal  # Sale price or primary price
    lease_price: Optional[Decimal] = None  # Required when transaction_status is SL
    currency: str = "PHP"
    zoning_classification: ZoningClassification
    title_number: str
    description: Optional[str] = None
    referred_by: Optional[str] = None
    transaction_status: TransactionStatus


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
    
    @validator('lease_price')
    def validate_lease_price(cls, v, values):
        transaction_status = values.get('transaction_status')
        if transaction_status == TransactionStatus.SL:
            if v is None or v <= 0:
                raise ValueError('Lease price is required and must be positive for Sale & Lease transactions')
        return v


class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # Google Places API data
    place_id: Optional[str] = None
    
    # Detailed address components (Google Places format)
    street: Optional[str] = None
    barangay_name: Optional[str] = None
    city_name: Optional[str] = None
    province_name: Optional[str] = None
    region_name: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    
    lot_area: Optional[float] = None
    property_type: Optional[PropertyType] = None
    price: Optional[Decimal] = None
    lease_price: Optional[Decimal] = None
    currency: Optional[str] = None
    zoning_classification: Optional[ZoningClassification] = None
    title_number: Optional[str] = None
    description: Optional[str] = None
    referred_by: Optional[str] = None
    transaction_status: Optional[TransactionStatus] = None
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
    is_marked: bool = False

    # Related objects - using UserPublic to exclude sensitive data
    submitted_by: Optional[UserPublic] = None
    reviewer: Optional[UserPublic] = None
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
    transaction_status: TransactionStatus
    created_at: datetime
    submitted_by: Optional[UserPublic] = None

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