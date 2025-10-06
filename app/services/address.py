"""
Address Service for Google Places API Integration
Handles address creation, updates, and queries with geographic data
"""

import json
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from geopy.distance import geodesic

from app.models.address import Address
from app.schemas.address import AddressCreate, AddressUpdate, AddressRead


class AddressService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_address(self, address_data: AddressCreate) -> Address:
        """Create a new address from Google Places data"""
        
        # Check if address with this place_id already exists
        if address_data.place_id:
            existing = await self.get_address_by_place_id(address_data.place_id)
            if existing:
                return existing
        
        # Create new address
        db_address = Address(
            place_id=address_data.place_id,
            formatted_address=address_data.formatted_address,
            latitude=address_data.latitude,
            longitude=address_data.longitude,
            street_number=address_data.street_number,
            route=address_data.route,
            unit_number=address_data.unit_number,
            building_name=address_data.building_name,
            barangay=address_data.barangay,
            city=address_data.city,
            province=address_data.province,
            region=address_data.region,
            postal_code=address_data.postal_code,
            country=address_data.country or "Philippines",
            place_types=json.dumps(address_data.place_types) if address_data.place_types else None
        )
        
        self.db.add(db_address)
        await self.db.commit()
        await self.db.refresh(db_address)
        
        return db_address
    
    async def get_address_by_place_id(self, place_id: str) -> Optional[Address]:
        """Get address by Google Places place_id"""
        stmt = select(Address).where(Address.place_id == place_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_address(self, address_id: int) -> Optional[Address]:
        """Get address by ID"""
        stmt = select(Address).where(Address.id == address_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def search_addresses_by_text(
        self, 
        query: str, 
        limit: int = 20
    ) -> List[Address]:
        """Search addresses by text across multiple fields"""
        search_term = f"%{query.lower()}%"
        
        stmt = (
            select(Address)
            .where(
                or_(
                    func.lower(Address.formatted_address).contains(search_term),
                    func.lower(Address.route).contains(search_term),
                    func.lower(Address.barangay).contains(search_term),
                    func.lower(Address.city).contains(search_term),
                    func.lower(Address.province).contains(search_term),
                    func.lower(Address.region).contains(search_term),
                    Address.postal_code.contains(query)
                )
            )
            .limit(limit)
            .order_by(Address.city, Address.province)
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_addresses_by_administrative_division(
        self,
        region: Optional[str] = None,
        province: Optional[str] = None,
        city: Optional[str] = None,
        barangay: Optional[str] = None,
        limit: int = 100
    ) -> List[Address]:
        """Get addresses filtered by administrative divisions"""
        stmt = select(Address)
        
        conditions = []
        if region:
            conditions.append(Address.region.ilike(f"%{region}%"))
        if province:
            conditions.append(Address.province.ilike(f"%{province}%"))
        if city:
            conditions.append(Address.city.ilike(f"%{city}%"))
        if barangay:
            conditions.append(Address.barangay.ilike(f"%{barangay}%"))
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        stmt = stmt.limit(limit).order_by(Address.region, Address.province, Address.city)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def find_nearby_addresses(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 5.0,
        limit: int = 50
    ) -> List[Tuple[Address, float]]:
        """Find addresses within a radius of given coordinates"""
        
        # Use PostgreSQL earthdistance extension if available, otherwise filter in Python
        # First get addresses within a rough bounding box for efficiency
        lat_delta = radius_km / 111.0  # Rough conversion: 1 degree ≈ 111 km
        lng_delta = radius_km / (111.0 * abs(math.cos(math.radians(latitude))))
        
        stmt = (
            select(Address)
            .where(
                and_(
                    Address.latitude.between(latitude - lat_delta, latitude + lat_delta),
                    Address.longitude.between(longitude - lng_delta, longitude + lng_delta),
                    Address.latitude.isnot(None),
                    Address.longitude.isnot(None)
                )
            )
            .limit(limit * 2)  # Get more than needed for distance filtering
        )
        
        result = await self.db.execute(stmt)
        addresses = result.scalars().all()
        
        # Calculate exact distances and filter
        nearby_addresses = []
        for address in addresses:
            if address.latitude and address.longitude:
                distance = geodesic(
                    (latitude, longitude),
                    (address.latitude, address.longitude)
                ).kilometers
                
                if distance <= radius_km:
                    nearby_addresses.append((address, distance))
        
        # Sort by distance
        nearby_addresses.sort(key=lambda x: x[1])
        return nearby_addresses[:limit]
    
    async def get_address_statistics(self) -> Dict[str, Any]:
        """Get statistics about addresses in the database"""
        
        # Count by region
        region_counts = await self.db.execute(
            select(Address.region, func.count(Address.id))
            .where(Address.region.isnot(None))
            .group_by(Address.region)
            .order_by(func.count(Address.id).desc())
        )
        
        # Count by province
        province_counts = await self.db.execute(
            select(Address.province, func.count(Address.id))
            .where(Address.province.isnot(None))
            .group_by(Address.province)
            .order_by(func.count(Address.id).desc())
        )
        
        # Count by city
        city_counts = await self.db.execute(
            select(Address.city, func.count(Address.id))
            .where(Address.city.isnot(None))
            .group_by(Address.city)
            .order_by(func.count(Address.id).desc())
            .limit(20)
        )
        
        # Total counts
        total_addresses = await self.db.execute(select(func.count(Address.id)))
        geocoded_addresses = await self.db.execute(
            select(func.count(Address.id))
            .where(and_(Address.latitude.isnot(None), Address.longitude.isnot(None)))
        )
        
        return {
            "total_addresses": total_addresses.scalar(),
            "geocoded_addresses": geocoded_addresses.scalar(),
            "by_region": dict(region_counts.fetchall()),
            "by_province": dict(province_counts.fetchall()),
            "top_cities": dict(city_counts.fetchall())
        }
    
    async def update_address(
        self, 
        address_id: int, 
        address_data: AddressUpdate
    ) -> Optional[Address]:
        """Update an existing address"""
        
        address = await self.get_address(address_id)
        if not address:
            return None
        
        # Update fields that are provided
        for field, value in address_data.dict(exclude_unset=True).items():
            if field == "place_types" and value:
                setattr(address, field, json.dumps(value))
            else:
                setattr(address, field, value)
        
        await self.db.commit()
        await self.db.refresh(address)
        
        return address
    
    async def delete_address(self, address_id: int) -> bool:
        """Delete an address (only if not referenced by properties)"""
        
        address = await self.get_address(address_id)
        if not address:
            return False
        
        # Check if address is referenced by any properties
        from app.models.property import Property
        property_count = await self.db.execute(
            select(func.count(Property.id)).where(Property.address_id == address_id)
        )
        
        if property_count.scalar() > 0:
            raise ValueError("Cannot delete address that is referenced by properties")
        
        await self.db.delete(address)
        await self.db.commit()
        
        return True


# Utility functions for address processing
def parse_google_places_address(places_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Google Places API response into structured address data"""
    
    components = {}
    
    if "address_components" in places_data:
        for component in places_data["address_components"]:
            types = component.get("types", [])
            long_name = component.get("long_name", "")
            
            if "street_number" in types:
                components["street_number"] = long_name
            elif "route" in types:
                components["route"] = long_name
            elif "sublocality_level_1" in types or "sublocality" in types:
                components["barangay"] = long_name
            elif "locality" in types or "administrative_area_level_2" in types:
                components["city"] = long_name
            elif "administrative_area_level_1" in types:
                components["province"] = long_name
            elif "country" in types:
                components["country"] = long_name
            elif "postal_code" in types:
                components["postal_code"] = long_name
    
    # Determine region from province (simplified mapping)
    if "province" in components:
        components["region"] = get_region_from_province(components["province"])
    
    return {
        "place_id": places_data.get("place_id"),
        "formatted_address": places_data.get("formatted_address", ""),
        "latitude": places_data.get("geometry", {}).get("location", {}).get("lat"),
        "longitude": places_data.get("geometry", {}).get("location", {}).get("lng"),
        "place_types": places_data.get("types", []),
        **components
    }


def get_region_from_province(province: str) -> str:
    """Map province to region (simplified version)"""
    
    region_mapping = {
        # NCR
        "Metro Manila": "National Capital Region (NCR)",
        
        # CALABARZON
        "Cavite": "CALABARZON (Region IV-A)",
        "Laguna": "CALABARZON (Region IV-A)",
        "Batangas": "CALABARZON (Region IV-A)",
        "Rizal": "CALABARZON (Region IV-A)",
        "Quezon": "CALABARZON (Region IV-A)",
        
        # Central Visayas
        "Cebu": "Central Visayas (Region VII)",
        "Bohol": "Central Visayas (Region VII)",
        "Negros Oriental": "Central Visayas (Region VII)",
        "Siquijor": "Central Visayas (Region VII)",
        
        # Add more mappings as needed
    }
    
    return region_mapping.get(province, province)


import math  # Add this import at the top
