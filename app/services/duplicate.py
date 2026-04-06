import re
from typing import List, Optional
from fuzzywuzzy import fuzz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.property import Property
from app.schemas.property import PropertyCreate
from app.schemas.workflow import DuplicateCheckRequest, DuplicateResult

# A property is only flagged as duplicate when BOTH address AND name
# score at or above these thresholds simultaneously.
_ADDRESS_THRESHOLD = 0.90
_NAME_THRESHOLD = 0.90

# Placeholder address/name strings that should never trigger a match
_PLACEHOLDER_VALUES = {'', 'n/a', 'na', 'none', 'tbd', 'tba', 'unknown', 'pending'}


def _normalize(value: str) -> str:
    return value.strip().lower()


def _is_placeholder(value: str) -> bool:
    return _normalize(value) in _PLACEHOLDER_VALUES


def _address_score(a: str, b: str) -> float:
    return fuzz.token_sort_ratio(a.lower(), b.lower()) / 100.0


def _name_score(a: str, b: str) -> float:
    return fuzz.token_sort_ratio(a.lower(), b.lower()) / 100.0


class DuplicateDetectionService:
    """
    Flags a property as a duplicate only when an existing property matches
    on BOTH address (≥90%) AND property name (≥90%) simultaneously.
    Notifications are only sent when both scores hit 100%.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _load_all_properties(self) -> List[Property]:
        result = await self.db.execute(
            select(Property).options(
                selectinload(Property.submitted_by),
                selectinload(Property.reviewer),
            )
        )
        return result.scalars().all()

    def _find_duplicate(
        self, address: str, name: str, properties: List[Property], exclude_id: int = None
    ) -> Optional[tuple]:
        """
        Return (property, addr_score, name_score) for the best match that
        exceeds both thresholds, or None if no match found.
        """
        if _is_placeholder(address) or _is_placeholder(name):
            return None

        best = None
        best_combined = 0.0

        for prop in properties:
            if exclude_id and prop.id == exclude_id:
                continue
            if not prop.address or not prop.name:
                continue

            addr = _address_score(address, prop.address)
            nm = _name_score(name, prop.name)

            if addr >= _ADDRESS_THRESHOLD and nm >= _NAME_THRESHOLD:
                combined = (addr + nm) / 2
                if combined > best_combined:
                    best_combined = combined
                    best = (prop, addr, nm)

        return best

    async def check_duplicates(
        self,
        property_data: PropertyCreate,
        threshold: float = _ADDRESS_THRESHOLD,
    ) -> List[DuplicateResult]:
        """Return duplicates based on address + name match."""
        properties = await self._load_all_properties()
        match = self._find_duplicate(
            property_data.address or "",
            property_data.name or "",
            properties,
        )
        if not match:
            return []

        prop, addr, nm = match
        combined = (addr + nm) / 2
        return [DuplicateResult(
            property_id=prop.id,
            similarity_score=combined,
            match_reasons=[
                f"Address match: {addr:.0%}",
                f"Name match: {nm:.0%}",
            ],
            property=prop,
        )]

    async def check_duplicates_by_criteria(
        self, criteria: DuplicateCheckRequest, threshold: float = _ADDRESS_THRESHOLD
    ) -> List[DuplicateResult]:
        """Check duplicates via address + name criteria (used by the /duplicates/check endpoint)."""
        if not criteria.address or not criteria.name:
            return []

        properties = await self._load_all_properties()
        match = self._find_duplicate(criteria.address, criteria.name, properties)
        if not match:
            return []

        prop, addr, nm = match
        combined = (addr + nm) / 2
        return [DuplicateResult(
            property_id=prop.id,
            similarity_score=combined,
            match_reasons=[
                f"Address match: {addr:.0%}",
                f"Name match: {nm:.0%}",
            ],
        )]

    async def calculate_similarity_score(
        self, prop1: Property, prop2: Property
    ) -> float:
        """Combined address + name similarity score between two properties."""
        if not prop1.address or not prop2.address or not prop1.name or not prop2.name:
            return 0.0
        addr = _address_score(prop1.address, prop2.address)
        nm = _name_score(prop1.name, prop2.name)
        return (addr + nm) / 2

    async def mark_property_as_duplicate(
        self,
        property_id: int,
        duplicate_of_id: int,
        notes: Optional[str] = None,
    ) -> Property:
        """Mark a property as a duplicate of another property."""
        stmt = (
            select(Property)
            .options(
                selectinload(Property.submitted_by),
                selectinload(Property.reviewer),
            )
            .where(Property.id == property_id)
        )
        result = await self.db.execute(stmt)
        property_obj = result.scalar_one_or_none()

        if not property_obj:
            raise ValueError(f"Property {property_id} not found")

        original_result = await self.db.execute(
            select(Property).where(Property.id == duplicate_of_id)
        )
        if not original_result.scalar_one_or_none():
            raise ValueError(f"Original property {duplicate_of_id} not found")

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
        threshold: float = _ADDRESS_THRESHOLD,
    ) -> List[DuplicateResult]:
        """Check for duplicates and notify only on a 100% combined match."""
        duplicates = await self.check_duplicates(property_data, threshold)

        if duplicates:
            from app.services.notification import NotificationService
            notification_service = NotificationService(self.db)

            for duplicate in duplicates:
                if duplicate.similarity_score == 1.0:
                    await notification_service.create_duplicate_notification(
                        user_id=user_id,
                        property_id=None,
                        duplicate_property_id=duplicate.property_id,
                        similarity_score=duplicate.similarity_score,
                        match_reasons=duplicate.match_reasons,
                    )

        return duplicates
