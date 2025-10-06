"""
Enhanced Address Model for Google Places API Integration
Stores address data in a structured, searchable format
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, DateTime, Integer, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Address(Base):
    """
    Structured address storage based on Google Places API data
    This allows for efficient searching, filtering, and geographic queries
    """
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Google Places API identifiers
    place_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True, index=True)
    formatted_address: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Coordinates for mapping and proximity searches
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    
    # Hierarchical address components (from most specific to general)
    street_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    route: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # Street name
    
    # Manual overrides for specific unit/building details
    unit_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    building_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Philippine administrative divisions (indexed for fast filtering)
    barangay: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    province: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    region: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Postal and country information
    postal_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)
    country: Mapped[str] = mapped_column(String(50), nullable=False, default="Philippines")
    
    # Google Places metadata
    place_types: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of types
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships (commented out until Property model is updated)
    # properties: Mapped[list["Property"]] = relationship("Property", back_populates="address")
    
    # Composite indexes for efficient queries
    __table_args__ = (
        # Geographic proximity searches
        Index('idx_coordinates', 'latitude', 'longitude'),
        # Administrative division searches
        Index('idx_admin_divisions', 'region', 'province', 'city', 'barangay'),
        # Address component searches
        Index('idx_address_components', 'city', 'province', 'postal_code'),
    )
    
    @property
    def complete_street_address(self) -> str:
        """Build complete street address with manual overrides"""
        parts = []
        
        # Manual overrides take precedence
        if self.unit_number:
            parts.append(f"Unit {self.unit_number}")
        
        if self.building_name:
            parts.append(self.building_name)
        
        # Street address
        if self.street_number and self.route:
            parts.append(f"{self.street_number} {self.route}")
        elif self.route:
            parts.append(self.route)
        
        return ", ".join(parts) if parts else ""
    
    @property
    def administrative_address(self) -> str:
        """Build administrative address (barangay, city, province)"""
        parts = []
        
        if self.barangay:
            parts.append(f"Brgy. {self.barangay}")
        if self.city:
            parts.append(self.city)
        if self.province:
            parts.append(self.province)
        if self.postal_code:
            parts.append(self.postal_code)
        
        return ", ".join(parts)
    
    @property
    def full_display_address(self) -> str:
        """Build full display address combining all components"""
        parts = []
        
        street = self.complete_street_address
        if street:
            parts.append(street)
        
        admin = self.administrative_address
        if admin:
            parts.append(admin)
        
        return ", ".join(parts) if parts else self.formatted_address
    
    def __repr__(self) -> str:
        return f"<Address(id={self.id}, city='{self.city}', province='{self.province}')>"


# Update Property model to use the Address relationship
class PropertyAddressMixin:
    """Mixin to add address relationship to Property model"""
    
    # Foreign key to Address table
    address_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("addresses.id"), 
        nullable=True,
        index=True
    )
    
    # Relationship to Address (commented out until properly implemented)
    # address: Mapped[Optional[Address]] = relationship("Address", back_populates="properties")
    
    # Keep the old address field for backward compatibility during migration
    legacy_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
