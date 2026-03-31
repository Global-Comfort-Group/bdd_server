import math
from typing import List, Tuple, Optional
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
        """
        Flag a property as duplicate if ANY of the following match an existing property:
          - Same title number (exact, case-insensitive, ignoring punctuation)
          - Same address (≥85% fuzzy match)
        """
        duplicates = []

        # 1. Exact title number match
        if criteria.title_number:
            exact_match = await self._check_exact_title_number(criteria.title_number)
            if exact_match:
                duplicates.append(DuplicateResult(
                    property_id=exact_match.id,
                    similarity_score=1.0,
                    match_reasons=["Same title number (TCT)"],
                ))

        # 2. Same address (high-threshold fuzzy match ≥ 0.85)
        if criteria.address:
            address_matches = await self._check_fuzzy_address_match(
                criteria.address, threshold=0.85
            )
            for match, score, reasons in address_matches:
                if match.id not in [d.property_id for d in duplicates]:
                    duplicates.append(DuplicateResult(
                        property_id=match.id,
                        similarity_score=score,
                        match_reasons=["Same address"],
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

    async def _check_exact_title_number(self, title_number: str) -> Property:
        """Check for exact title number match (case-insensitive, strips punctuation)."""
        import re
        normalized = re.sub(r'[^a-z0-9]', '', title_number.lower())
        if not normalized or normalized in ('na', 'none', 'tbd'):
            return None

        stmt = (
            select(Property)
            .options(
                selectinload(Property.submitted_by),
                selectinload(Property.reviewer)
            )
        )
        result = await self.db.execute(stmt)
        properties = result.scalars().all()

        for prop in properties:
            if not prop.title_number:
                continue
            prop_normalized = re.sub(r'[^a-z0-9]', '', prop.title_number.lower())
            if prop_normalized == normalized:
                return prop
        return None

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
    
    async def mark_property_as_duplicate(
        self,
        property_id: int,
        duplicate_of_id: int,
        notes: Optional[str] = None
    ) -> Property:
        """Mark a property as a duplicate of another property"""
        stmt = (
            select(Property)
            .options(
                selectinload(Property.submitted_by),
                selectinload(Property.reviewer)
            )
            .where(Property.id == property_id)
        )
        result = await self.db.execute(stmt)
        property_obj = result.scalar_one_or_none()
        
        if not property_obj:
            raise ValueError(f"Property {property_id} not found")
        
        # Verify the original property exists
        original_stmt = select(Property).where(Property.id == duplicate_of_id)
        original_result = await self.db.execute(original_stmt)
        original_property = original_result.scalar_one_or_none()
        
        if not original_property:
            raise ValueError(f"Original property {duplicate_of_id} not found")
        
        # Mark as duplicate
        property_obj.is_duplicate = True
        property_obj.duplicate_of_id = duplicate_of_id
        property_obj.duplicate_notes = notes
        
        await self.db.commit()
        await self.db.refresh(property_obj)
        
        return property_obj
    
    async def check_and_notify_duplicates(
        self,
        property_data: PropertyCreate,
        user_id: int,
        threshold: float = 0.75
    ) -> List[DuplicateResult]:
        """
        Check for duplicates and create notifications if found.
        Returns list of duplicates found.
        """
        duplicates = await self.check_duplicates(property_data, threshold)
        
        if duplicates:
            # Import notification service
            from app.services.notification import NotificationService
            notification_service = NotificationService(self.db)
            
            # Create notification for high-confidence duplicates
            for duplicate in duplicates:
                if duplicate.similarity_score >= threshold:
                    await notification_service.create_duplicate_notification(
                        user_id=user_id,
                        property_id=None,  # Property not created yet
                        duplicate_property_id=duplicate.property_id,
                        similarity_score=duplicate.similarity_score,
                        match_reasons=duplicate.match_reasons
                    )
        
        return duplicates