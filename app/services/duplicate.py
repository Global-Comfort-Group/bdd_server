import math
from typing import List, Tuple
from fuzzywuzzy import fuzz
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.property import Property
from app.schemas.property import PropertyCreate
from app.schemas.workflow import DuplicateCheckRequest, DuplicateResult


class DuplicateDetectionService:
    """Service for detecting duplicate properties using multiple matching algorithms."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_duplicates(
        self, 
        property_data: PropertyCreate, 
        threshold: float = 0.7
    ) -> List[DuplicateResult]:
        """
        Check for duplicate properties based on multiple criteria.
        
        Args:
            property_data: Property data to check for duplicates
            threshold: Minimum similarity score to consider a match
            
        Returns:
            List of potential duplicates with similarity scores
        """
        duplicates = []

        # 1. Check exact title number match (highest priority)
        exact_match = await self._check_exact_title_match(property_data.title_number)
        if exact_match:
            duplicates.append(DuplicateResult(
                property_id=exact_match.id,
                similarity_score=1.0,
                match_reasons=["Exact title number match"],
                property=exact_match
            ))

        # 2. Check fuzzy address matching
        address_matches = await self._check_fuzzy_address_match(
            property_data.address, threshold
        )
        for match, score, reasons in address_matches:
            if match.id not in [d.property_id for d in duplicates]:
                duplicates.append(DuplicateResult(
                    property_id=match.id,
                    similarity_score=score,
                    match_reasons=reasons,
                    property=match
                ))

        # 3. Check coordinate proximity (if coordinates provided)
        if property_data.latitude and property_data.longitude:
            location_matches = await self._check_location_proximity(
                property_data.latitude,
                property_data.longitude,
                property_data.name,
                threshold
            )
            for match, score, reasons in location_matches:
                if match.id not in [d.property_id for d in duplicates]:
                    duplicates.append(DuplicateResult(
                        property_id=match.id,
                        similarity_score=score,
                        match_reasons=reasons,
                        property=match
                    ))

        # Sort by similarity score (highest first)
        duplicates.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return duplicates

    async def check_duplicates_by_criteria(
        self, criteria: DuplicateCheckRequest, threshold: float = 0.7
    ) -> List[DuplicateResult]:
        """Check for duplicates using flexible criteria."""
        duplicates = []

        # Check title number if provided
        if criteria.title_number:
            exact_match = await self._check_exact_title_match(criteria.title_number)
            if exact_match:
                duplicates.append(DuplicateResult(
                    property_id=exact_match.id,
                    similarity_score=1.0,
                    match_reasons=["Exact title number match"],
                    property=exact_match
                ))

        # Check address if provided
        if criteria.address:
            address_matches = await self._check_fuzzy_address_match(
                criteria.address, threshold
            )
            for match, score, reasons in address_matches:
                if match.id not in [d.property_id for d in duplicates]:
                    duplicates.append(DuplicateResult(
                        property_id=match.id,
                        similarity_score=score,
                        match_reasons=reasons,
                        property=match
                    ))

        # Check coordinates if provided
        if criteria.latitude and criteria.longitude:
            location_matches = await self._check_location_proximity(
                criteria.latitude,
                criteria.longitude,
                criteria.name,
                threshold
            )
            for match, score, reasons in location_matches:
                if match.id not in [d.property_id for d in duplicates]:
                    duplicates.append(DuplicateResult(
                        property_id=match.id,
                        similarity_score=score,
                        match_reasons=reasons,
                        property=match
                    ))

        duplicates.sort(key=lambda x: x.similarity_score, reverse=True)
        return duplicates

    async def calculate_similarity_score(
        self, prop1: Property, prop2: Property
    ) -> float:
        """Calculate comprehensive similarity score between two properties."""
        scores = []
        
        # Title number match (exact)
        if prop1.title_number == prop2.title_number:
            return 1.0
        
        # Address similarity (fuzzy matching)
        address_score = fuzz.ratio(prop1.address.lower(), prop2.address.lower()) / 100.0
        scores.append(address_score * 0.4)  # 40% weight
        
        # Name similarity
        name_score = fuzz.ratio(prop1.name.lower(), prop2.name.lower()) / 100.0
        scores.append(name_score * 0.3)  # 30% weight
        
        # Location proximity (if both have coordinates)
        if (prop1.latitude and prop1.longitude and 
            prop2.latitude and prop2.longitude):
            distance = self._calculate_distance(
                prop1.latitude, prop1.longitude,
                prop2.latitude, prop2.longitude
            )
            # Consider properties within 100m as very similar
            location_score = max(0, 1 - (distance / 100))
            scores.append(location_score * 0.3)  # 30% weight
        
        return sum(scores) if scores else 0.0

    async def _check_exact_title_match(self, title_number: str) -> Property:
        """Check for exact title number match."""
        stmt = (
            select(Property)
            .options(
                selectinload(Property.submitted_by),
                selectinload(Property.reviewer)
            )
            .where(Property.title_number == title_number)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _check_fuzzy_address_match(
        self, address: str, threshold: float = 0.7
    ) -> List[Tuple[Property, float, List[str]]]:
        """Check for fuzzy address matches."""
        stmt = (
            select(Property)
            .options(
                selectinload(Property.submitted_by),
                selectinload(Property.reviewer)
            )
        )
        result = await self.db.execute(stmt)
        properties = result.scalars().all()
        
        matches = []
        for prop in properties:
            # Calculate address similarity
            address_score = fuzz.ratio(address.lower(), prop.address.lower()) / 100.0
            
            if address_score >= threshold:
                reasons = [f"Address similarity: {address_score:.2%}"]
                matches.append((prop, address_score, reasons))
        
        return matches

    async def _check_location_proximity(
        self,
        latitude: float,
        longitude: float,
        name: str = None,
        threshold: float = 0.7,
        radius_meters: float = 500.0
    ) -> List[Tuple[Property, float, List[str]]]:
        """Check for properties within geographic proximity."""
        stmt = (
            select(Property)
            .options(
                selectinload(Property.submitted_by),
                selectinload(Property.reviewer)
            )
            .where(
                Property.latitude.isnot(None),
                Property.longitude.isnot(None)
            )
        )
        result = await self.db.execute(stmt)
        properties = result.scalars().all()
        
        matches = []
        for prop in properties:
            distance = self._calculate_distance(
                latitude, longitude,
                prop.latitude, prop.longitude
            )
            
            if distance <= radius_meters:
                # Calculate combined score based on distance and name similarity
                distance_score = max(0, 1 - (distance / radius_meters))
                
                total_score = distance_score
                reasons = [f"Within {distance:.1f}m"]
                
                # Add name similarity if name provided
                if name:
                    name_score = fuzz.ratio(name.lower(), prop.name.lower()) / 100.0
                    total_score = (distance_score * 0.6) + (name_score * 0.4)
                    reasons.append(f"Name similarity: {name_score:.2%}")
                
                if total_score >= threshold:
                    matches.append((prop, total_score, reasons))
        
        return matches

    def _calculate_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """
        Calculate distance between two coordinate points using Haversine formula.
        Returns distance in meters.
        """
        # Earth's radius in meters
        R = 6371000
        
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