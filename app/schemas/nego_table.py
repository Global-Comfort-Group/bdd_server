from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from app.models.enums import TransactionMode
from app.models.nego_table import NegoTableStatus

# Base schemas
class NegotiationEntryBase(BaseModel):
    date: datetime
    owner_representative: str
    subject_matter: str
    venue: Optional[str] = None
    time: Optional[str] = None
    mode_of_transaction: TransactionMode = TransactionMode.FACE_TO_FACE
    floor_area: Optional[float] = None
    rental_per_month: Optional[float] = None
    rental_per_sqm: Optional[float] = None
    sale_price: Optional[float] = None
    sale_price_per_sqm: Optional[float] = None
    lease_term: Optional[int] = None
    escalation: Optional[float] = None
    escalation_start_year: Optional[int] = None
    rent_free_period: Optional[int] = None
    advance_rent: Optional[int] = None
    security_deposit: Optional[int] = None
    other_concerns: Optional[str] = None
    notes: Optional[str] = None

class NegotiationEntryCreate(NegotiationEntryBase):
    pass

class NegotiationEntryUpdate(BaseModel):
    date: Optional[datetime] = None
    owner_representative: Optional[str] = None
    subject_matter: Optional[str] = None
    venue: Optional[str] = None
    time: Optional[str] = None
    mode_of_transaction: Optional[TransactionMode] = None
    floor_area: Optional[float] = None
    rental_per_month: Optional[float] = None
    rental_per_sqm: Optional[float] = None
    sale_price: Optional[float] = None
    sale_price_per_sqm: Optional[float] = None
    lease_term: Optional[int] = None
    escalation: Optional[float] = None
    escalation_start_year: Optional[int] = None
    rent_free_period: Optional[int] = None
    advance_rent: Optional[int] = None
    security_deposit: Optional[int] = None
    other_concerns: Optional[str] = None
    notes: Optional[str] = None

class NegotiationEntry(NegotiationEntryBase):
    id: int
    nego_table_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Nego Table schemas
class NegoTableBase(BaseModel):
    property_id: int
    referred_date: datetime
    source_origin: str
    contact_person: Optional[str] = None
    contact_position: Optional[str] = None
    
    # Property comparison
    original_property_name: str
    current_property_name: str
    original_owner: Optional[str] = None
    current_owner: Optional[str] = None
    original_location: str
    current_location: str
    original_property_type: str
    current_property_type: str
    original_lot_area: float
    current_lot_area: float
    original_cfa: Optional[float] = None
    current_cfa: Optional[float] = None
    original_frontage: Optional[float] = None
    current_frontage: Optional[float] = None
    original_depth: Optional[float] = None
    current_depth: Optional[float] = None
    original_nor: Optional[int] = None
    current_nor: Optional[int] = None
    original_parking: Optional[str] = None
    current_parking: Optional[str] = None
    original_zonal_value: Optional[str] = None
    current_zonal_value: Optional[str] = None
    original_orientation: Optional[str] = None
    current_orientation: Optional[str] = None
    original_lot_shape: Optional[str] = None
    current_lot_shape: Optional[str] = None
    
    # Financial information
    sale_total: Optional[float] = None
    sale_per_sqm: Optional[float] = None
    lease_rate: Optional[float] = None
    monthly_lease: Optional[float] = None
    intended_rooms: Optional[int] = None
    investment: Optional[float] = None
    pby_roi_operations: Optional[float] = None
    pby_roi_properties: Optional[float] = None
    pby_roi_combined: Optional[float] = None
    
    # Ownership info
    name_in_tct: Optional[str] = None
    living_status: Optional[str] = None
    residency_status: Optional[str] = None
    
    status: NegoTableStatus = NegoTableStatus.ACTIVE

class NegoTableCreate(NegoTableBase):
    negotiations: List[NegotiationEntryCreate] = []

class NegoTableUpdate(BaseModel):
    referred_date: Optional[datetime] = None
    source_origin: Optional[str] = None
    contact_person: Optional[str] = None
    contact_position: Optional[str] = None
    original_property_name: Optional[str] = None
    current_property_name: Optional[str] = None
    original_owner: Optional[str] = None
    current_owner: Optional[str] = None
    original_location: Optional[str] = None
    current_location: Optional[str] = None
    original_property_type: Optional[str] = None
    current_property_type: Optional[str] = None
    original_lot_area: Optional[float] = None
    current_lot_area: Optional[float] = None
    original_cfa: Optional[float] = None
    current_cfa: Optional[float] = None
    original_frontage: Optional[float] = None
    current_frontage: Optional[float] = None
    original_depth: Optional[float] = None
    current_depth: Optional[float] = None
    original_nor: Optional[int] = None
    current_nor: Optional[int] = None
    original_parking: Optional[str] = None
    current_parking: Optional[str] = None
    original_zonal_value: Optional[str] = None
    current_zonal_value: Optional[str] = None
    original_orientation: Optional[str] = None
    current_orientation: Optional[str] = None
    original_lot_shape: Optional[str] = None
    current_lot_shape: Optional[str] = None
    sale_total: Optional[float] = None
    sale_per_sqm: Optional[float] = None
    lease_rate: Optional[float] = None
    monthly_lease: Optional[float] = None
    intended_rooms: Optional[int] = None
    investment: Optional[float] = None
    pby_roi_operations: Optional[float] = None
    pby_roi_properties: Optional[float] = None
    pby_roi_combined: Optional[float] = None
    name_in_tct: Optional[str] = None
    living_status: Optional[str] = None
    residency_status: Optional[str] = None
    status: Optional[NegoTableStatus] = None

class NegoTable(NegoTableBase):
    id: int
    created_by_id: int
    updated_by_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    negotiations: List[NegotiationEntry] = []

    class Config:
        from_attributes = True

# Response schemas with property info
class NegoTableWithProperty(NegoTable):
    property: dict  # Property info will be included