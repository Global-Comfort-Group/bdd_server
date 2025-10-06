"""
Address Schemas for Google Places API Integration
Pydantic models for address data validation and serialization
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, validator, Field


class AddressBase(BaseModel):
    """Base address schema with common fields"""
    
    # Google Places API data
    place_id: Optional[str] = None
    formatted_address: str = Field(..., min_length=1, max_length=500)
    
    # Coordinates
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    
    # Street address components
    street_number: Optional[str] = Field(None, max_length=20)
    route: Optional[str] = Field(None, max_length=200)  # Street name
    
    # Manual overrides
    unit_number: Optional[str] = Field(None, max_length=50)
    building_name: Optional[str] = Field(None, max_length=200)
    
    # Administrative divisions
    barangay: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    
    # Postal and country
    postal_code: Optional[str] = Field(None, max_length=10)
    country: str = Field(default="Philippines", max_length=50)
    
    # Google Places metadata
    place_types: Optional[List[str]] = None
    
    @validator('postal_code')
    def validate_postal_code(cls, v):
        if v and not v.isdigit():
            raise ValueError('Postal code must contain only digits')
        return v
    
    @validator('place_types')
    def validate_place_types(cls, v):
        if v and len(v) > 20:  # Reasonable limit
            raise ValueError('Too many place types')
        return v


class AddressCreate(AddressBase):
    """Schema for creating a new address"""
    
    @validator('formatted_address')
    def validate_formatted_address(cls, v):
        if not v or not v.strip():
            raise ValueError('Formatted address cannot be empty')
        return v.strip()


class AddressUpdate(BaseModel):
    """Schema for updating an existing address"""
    
    formatted_address: Optional[str] = Field(None, min_length=1, max_length=500)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    
    street_number: Optional[str] = Field(None, max_length=20)
    route: Optional[str] = Field(None, max_length=200)
    
    unit_number: Optional[str] = Field(None, max_length=50)
    building_name: Optional[str] = Field(None, max_length=200)
    
    barangay: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    
    postal_code: Optional[str] = Field(None, max_length=10)
    country: Optional[str] = Field(None, max_length=50)
    
    place_types: Optional[List[str]] = None


class AddressRead(AddressBase):
    """Schema for reading address data"""
    
    id: int
    created_at: datetime
    updated_at: datetime
    
    # Computed properties
    complete_street_address: Optional[str] = None
    administrative_address: Optional[str] = None
    full_display_address: Optional[str] = None
    
    class Config:
        from_attributes = True


class AddressSearchResult(BaseModel):
    """Schema for address search results"""
    
    address: AddressRead
    distance_km: Optional[float] = None  # For proximity searches
    relevance_score: Optional[float] = None  # For text searches


class AddressStatistics(BaseModel):
    """Schema for address statistics"""
    
    total_addresses: int
    geocoded_addresses: int
    by_region: dict[str, int]
    by_province: dict[str, int]
    top_cities: dict[str, int]


class AddressSearchQuery(BaseModel):
    """Schema for address search queries"""
    
    # Text search
    query: Optional[str] = None
    
    # Administrative division filters
    region: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    barangay: Optional[str] = None
    
    # Geographic filters
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    radius_km: Optional[float] = Field(None, gt=0, le=100)  # Max 100km radius
    
    # Pagination
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    
    @validator('radius_km')
    def validate_radius_with_coordinates(cls, v, values):
        if v and (not values.get('latitude') or not values.get('longitude')):
            raise ValueError('Latitude and longitude required for radius search')
        return v


class GooglePlacesAddressData(BaseModel):
    """Schema for Google Places API address data (from client)"""
    
    formatted_address: str
    place_id: str
    
    # Parsed components
    street_number: Optional[str] = None
    route: Optional[str] = None
    barangay: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    region: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = "Philippines"
    
    # Manual overrides
    manual_unit: Optional[str] = None
    manual_street: Optional[str] = None
    
    # Coordinates
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    
    # Additional info
    types: List[str] = []
    
    def to_address_create(self) -> AddressCreate:
        """Convert to AddressCreate schema"""
        return AddressCreate(
            place_id=self.place_id,
            formatted_address=self.formatted_address,
            latitude=self.lat,
            longitude=self.lng,
            street_number=self.street_number,
            route=self.route,
            unit_number=self.manual_unit,
            barangay=self.barangay,
            city=self.city,
            province=self.province,
            region=self.region,
            postal_code=self.postal_code,
            country=self.country or "Philippines",
            place_types=self.types
        )
