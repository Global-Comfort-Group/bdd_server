from typing import Optional, Tuple
import asyncio
from geopy.geocoders import GoogleV3
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings


class GeocodingService:
    """Service for geocoding addresses and coordinates."""
    
    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.geolocator = GoogleV3(api_key=self.api_key) if self.api_key else None
        self.executor = ThreadPoolExecutor(max_workers=3)
    
    def _geocode_sync(self, address: str) -> Optional[Tuple[float, float]]:
        """Geocode address synchronously."""
        if not self.geolocator:
            return None
        
        try:
            location = self.geolocator.geocode(address)
            if location:
                return (location.latitude, location.longitude)
            return None
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None
    
    def _reverse_geocode_sync(
        self, latitude: float, longitude: float
    ) -> Optional[str]:
        """Reverse geocode coordinates synchronously."""
        if not self.geolocator:
            return None
        
        try:
            location = self.geolocator.reverse(f"{latitude}, {longitude}")
            if location:
                return location.address
            return None
        except Exception as e:
            print(f"Reverse geocoding error: {e}")
            return None
    
    async def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Convert address to coordinates.
        
        Args:
            address: Address string to geocode
            
        Returns:
            Tuple of (latitude, longitude) or None if geocoding fails
        """
        if not address or not self.geolocator:
            return None
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self._geocode_sync, 
            address
        )
    
    async def reverse_geocode(
        self, latitude: float, longitude: float
    ) -> Optional[str]:
        """
        Convert coordinates to address.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Address string or None if reverse geocoding fails
        """
        if not self.geolocator:
            return None
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self._reverse_geocode_sync, 
            latitude, 
            longitude
        )
    
    async def validate_coordinates(
        self, latitude: float, longitude: float
    ) -> bool:
        """
        Validate if coordinates are valid by attempting reverse geocoding.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            True if coordinates are valid, False otherwise
        """
        # Basic validation
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            return False
        
        # Try reverse geocoding to validate
        address = await self.reverse_geocode(latitude, longitude)
        return address is not None
    
    def calculate_distance_km(
        self, 
        lat1: float, lon1: float, 
        lat2: float, lon2: float
    ) -> float:
        """
        Calculate distance between two points in kilometers using Haversine formula.
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            
        Returns:
            Distance in kilometers
        """
        import math
        
        # Earth's radius in kilometers
        R = 6371.0
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Differences
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Haversine formula
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c