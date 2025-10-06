from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.enums import TransactionMode
import enum

class NegoTableStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ON_HOLD = "ON_HOLD"
    CANCELLED = "CANCELLED"

class NegoTable(Base):
    __tablename__ = "nego_tables"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    
    # Source Information
    referred_date = Column(DateTime, nullable=False)
    source_origin = Column(String(255), nullable=False)
    contact_person = Column(String(255))
    contact_position = Column(String(255))
    
    # Property Overview (original vs current)
    original_property_name = Column(String(255), nullable=False)
    current_property_name = Column(String(255), nullable=False)
    original_owner = Column(String(255))
    current_owner = Column(String(255))
    original_location = Column(Text, nullable=False)
    current_location = Column(Text, nullable=False)
    original_property_type = Column(String(255), nullable=False)
    current_property_type = Column(String(255), nullable=False)
    original_lot_area = Column(Float, nullable=False)
    current_lot_area = Column(Float, nullable=False)
    original_cfa = Column(Float)
    current_cfa = Column(Float)
    original_frontage = Column(Float)
    current_frontage = Column(Float)
    original_depth = Column(Float)
    current_depth = Column(Float)
    original_nor = Column(Integer)  # Number of Rooms
    current_nor = Column(Integer)
    original_parking = Column(String(255))
    current_parking = Column(String(255))
    original_zonal_value = Column(String(255))
    current_zonal_value = Column(String(255))
    original_orientation = Column(String(255))
    current_orientation = Column(String(255))
    original_lot_shape = Column(String(255))
    current_lot_shape = Column(String(255))
    
    # Financial Analysis
    sale_total = Column(Float)
    sale_per_sqm = Column(Float)
    lease_rate = Column(Float)
    monthly_lease = Column(Float)
    intended_rooms = Column(Integer)
    investment = Column(Float)
    
    # PBY ROI
    pby_roi_operations = Column(Float)
    pby_roi_properties = Column(Float)
    pby_roi_combined = Column(Float)
    
    # Ownership Information
    name_in_tct = Column(String(255))
    living_status = Column(String(100))
    residency_status = Column(String(100))
    
    # Status and Tracking
    status = Column(SQLEnum(NegoTableStatus), default=NegoTableStatus.ACTIVE)
    created_by_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    updated_by_id = Column(Integer, ForeignKey("user.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    property = relationship("Property", back_populates="nego_tables")
    created_by = relationship("User", foreign_keys=[created_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])
    negotiations = relationship("NegotiationEntry", back_populates="nego_table", cascade="all, delete-orphan")
    chronicle_attachments = relationship("NegotiationChronicleAttachment", back_populates="nego_table", cascade="all, delete-orphan")

class NegotiationEntry(Base):
    __tablename__ = "negotiation_entries"

    id = Column(Integer, primary_key=True, index=True)
    nego_table_id = Column(Integer, ForeignKey("nego_tables.id"), nullable=False)
    
    date = Column(DateTime, nullable=False)
    owner_representative = Column(String(255), nullable=False)
    subject_matter = Column(Text, nullable=False)
    venue = Column(String(255))
    time = Column(String(100))
    mode_of_transaction = Column(SQLEnum(TransactionMode), default=TransactionMode.FACE_TO_FACE)
    
    # Financial data for this negotiation
    floor_area = Column(Float)
    rental_per_month = Column(Float)
    rental_per_sqm = Column(Float)
    sale_price = Column(Float)
    sale_price_per_sqm = Column(Float)
    lease_term = Column(Integer)  # in years
    escalation = Column(Float)  # percentage
    escalation_start_year = Column(Integer)
    rent_free_period = Column(Integer)  # in months
    advance_rent = Column(Integer)  # in months
    security_deposit = Column(Integer)  # in months
    
    other_concerns = Column(Text)
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    nego_table = relationship("NegoTable", back_populates="negotiations")