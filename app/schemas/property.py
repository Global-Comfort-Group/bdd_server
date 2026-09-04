from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, model_validator, validator

from app.models.enums import PropertyType, PropertyStatus, TransactionStatus
from app.models.types import ZoningClassification
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
    building_area: Optional[float] = None
    floors: Optional[int] = None
    parking_slots: Optional[int] = None
    rooms: Optional[int] = None
    currency: str = "PHP"
    zoning_classification: ZoningClassification
    title_number: Optional[str] = None
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
    
    @model_validator(mode='after')
    def validate_lease_price(self):
        """Lease price is required for Sale & Lease.

        This must be a MODEL validator, not a field validator on lease_price:
        `lease_price` is declared before `transaction_status`, so a field
        validator runs before transaction_status has been populated and its
        `values.get('transaction_status')` is always None — the rule silently
        never fired. Running after the whole model is built fixes that.
        """
        if self.transaction_status == TransactionStatus.SL:
            if self.lease_price is None or self.lease_price <= 0:
                raise ValueError(
                    'Lease price is required and must be positive for Sale & Lease transactions'
                )
        return self


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
    building_area: Optional[float] = None
    floors: Optional[int] = None
    parking_slots: Optional[int] = None
    rooms: Optional[int] = None
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
    is_imported: bool = False

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
    is_imported: bool = False
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
    document_type: Optional[str] = None  # 'pby_ffs', 'due_diligence', or None for general


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


# ── Excel Bulk Import Schemas ────────────────────────────────────────────────

class ExcelPropertyPreviewRow(BaseModel):
    """A single property row parsed from the Excel file, returned for user preview."""
    row_id: str           # Unique key: "<sheet_name>|<row_number>"
    sheet_name: str
    row_number: int
    name: Optional[str] = None
    address: Optional[str] = None
    referred_by: Optional[str] = None
    status_hint: Optional[str] = None

    # Resolved per-sheet from the header text; absent on sheets that lack the
    # column (the Jan/Aug-Dec layout has no area or lease/sale columns).
    referral_type: Optional[str] = None    # Broker / Council / BDD / Employee
    lot_area: Optional[float] = None
    building_area: Optional[float] = None  # "CFA (Sqm.)" in the source
    lease_raw: Optional[str] = None        # raw text, e.g. "300/sqm."
    sale_raw: Optional[str] = None         # raw text, e.g. "94Million"

    # Duplicate advice from the preview step. Advisory only — the admin can
    # still select a flagged row. Enforcement happens at confirm time.
    duplicate_kind: Optional[str] = None    # "existing" | "in_file" | None
    duplicate_of: Optional[str] = None      # human-readable match description
    duplicate_score: Optional[float] = None # similarity of the weaker signal


class ExcelParseResponse(BaseModel):
    """Response from the preview endpoint — includes a token to reference cached rows."""
    import_token: str     # UUID — used in the confirm step
    total_rows: int
    duplicate_count: int = 0   # how many of `rows` carry a duplicate_kind
    rows: List[ExcelPropertyPreviewRow]


class ExcelImportConfirmRequest(BaseModel):
    """Request body for the confirm endpoint."""
    import_token: str                 # Token returned by the preview endpoint
    row_ids: List[str]                # Subset of row_ids the user selected to import


class ExcelImportResult(BaseModel):
    """Response from the confirm endpoint.

    Confirming does NOT create properties — it adds rows to the review queue
    (`property_imports`). They become properties only when an admin promotes
    them and supplies the fields the Excel sheet does not carry.
    """
    staged_count: int                 # rows added to the review queue
    skipped_count: int
    duplicate_skipped_count: int = 0  # subset of skipped that were duplicates
    errors: List[str]


class PropertyImportRead(BaseModel):
    """A staged lead awaiting review. Every sheet-absent value is None —
    never 0 and never a default."""
    id: int
    name: str
    address: Optional[str] = None
    referred_by: Optional[str] = None
    referral_type: Optional[str] = None
    lot_area: Optional[float] = None
    building_area: Optional[float] = None
    lease_raw: Optional[str] = None
    sale_raw: Optional[str] = None
    status_hint: Optional[str] = None
    sheet_name: Optional[str] = None
    row_number: Optional[int] = None
    source_file: Optional[str] = None
    review_status: str
    review_notes: Optional[str] = None
    promoted_property_id: Optional[int] = None
    created_at: datetime

    # What promotion still needs from a human, computed server-side.
    missing_required: List[str] = []

    class Config:
        from_attributes = True


class PromotionResult(BaseModel):
    """Result of promoting a staged lead.

    Deliberately NOT PropertyRead: that model pulls `attachments` and
    `workflow_history`, which are unloaded relationships on a freshly created
    Property and blow up async serialization. The caller only needs to know
    which property was created and the lead's new state.
    """
    property_id: int
    property_name: str
    import_row: PropertyImportRead


class PropertyImportListResponse(BaseModel):
    total: int
    pending: int
    promoted: int
    discarded: int
    items: List[PropertyImportRead]


class PromoteImportRequest(BaseModel):
    """Fields the Excel sheet cannot supply, provided by the admin.

    lot_area and transaction_status may be omitted when the staged row already
    has them; the rest are always required because no sheet layout carries them.
    """
    price: Decimal
    property_type: PropertyType
    # Same Literal the manual submission path uses — a loose `str` here would
    # let promotion write zoning values the property form rejects.
    zoning_classification: ZoningClassification
    lot_area: Optional[float] = None
    transaction_status: Optional[TransactionStatus] = None
    lease_price: Optional[Decimal] = None
    building_area: Optional[float] = None
    name: Optional[str] = None
    address: Optional[str] = None
    referred_by: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    title_number: Optional[str] = None
    floors: Optional[int] = None
    parking_slots: Optional[int] = None
    rooms: Optional[int] = None
    currency: Optional[str] = None


