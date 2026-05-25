import math
import re
from typing import List, Optional, Tuple
from fuzzywuzzy import fuzz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.property import Property
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.property import PropertyCreate
from app.schemas.workflow import DuplicateCheckRequest, DuplicateResult


# === Duplicate detection rules ===
#
# Two properties are duplicates only when ALL of these match simultaneously:
#   1. Address text similarity ≥ 85%  OR  GPS coordinates within ~30 meters
#   2. Lot area within ±5% (or both unknown)
#   3. Transaction type is identical (Sale != Lease, etc.)
#   4. For HOTEL property type ONLY: building (floor) area within ±5%
#
# Property name and title number are NOT used as duplicate signals — they
# can drift between submissions of the same physical asset.

_ADDRESS_THRESHOLD = 0.85
_AREA_TOLERANCE = 0.05  # ±5%
_COORD_RADIUS_METERS = 30.0
_HOTEL_TYPE = "HOTEL"

_PLACEHOLDER_VALUES = {'', 'n/a', 'na', 'none', 'tbd', 'tba', 'unknown', 'pending', '-'}

# Generic geographic terms that appear in nearly every PH address. They inflate
# similarity between properties that are merely in the same city/province, so
# we strip them before scoring.
_GEO_NOISE = {
    'philippines', 'ph', 'metro', 'city', 'province', 'region', 'municipality',
    'barangay', 'brgy', 'cebu', 'manila', 'makati', 'quezon', 'pasig', 'taguig',
    'muntinlupa', 'paranaque', 'laspinas', 'caloocan', 'malabon', 'navotas',
    'valenzuela', 'marikina', 'pasay', 'pateros', 'mandaluyong', 'sanmateo',
    'laguna', 'batangas', 'cavite', 'bulacan', 'pampanga', 'bataan', 'zambales',
    'davao', 'cagayan', 'iloilo', 'bacolod', 'zamboanga', 'mandaue', 'lapu',
    'lapulapu', 'talisay', 'minglanilla', 'naga', 'consolacion', 'liloan',
    'compostela', 'olongapo',
}


def _is_placeholder(value: Optional[str]) -> bool:
    return (value or '').strip().lower() in _PLACEHOLDER_VALUES


def _normalize_address(address: Optional[str]) -> str:
    """Strip street suffixes, punctuation, and generic geo terms so the
    comparison focuses on the distinguishing parts (street name, building,
    barangay)."""
    if not address:
        return ''
    text = address.lower()
    text = re.sub(r'\b(st|street|ave|avenue|rd|road|dr|drive|blvd|boulevard)\b', ' ', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    tokens = [t for t in text.split() if len(t) > 1 and t not in _GEO_NOISE]
    return ' '.join(tokens)


def _address_score(a: Optional[str], b: Optional[str]) -> float:
    na, nb = _normalize_address(a), _normalize_address(b)
    if not na or not nb:
        return 0.0
    return fuzz.token_sort_ratio(na, nb) / 100.0


def _haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371000.0  # earth radius, meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _location_matches(
    addr_score: float,
    lat1: Optional[float], lng1: Optional[float],
    lat2: Optional[float], lng2: Optional[float],
) -> bool:
    """A location matches when either the address text is similar enough
    OR the GPS coordinates are within ~30 m of each other."""
    if addr_score >= _ADDRESS_THRESHOLD:
        return True
    if lat1 is not None and lng1 is not None and lat2 is not None and lng2 is not None:
        return _haversine_meters(lat1, lng1, lat2, lng2) <= _COORD_RADIUS_METERS
    return False


def _area_matches(a: Optional[float], b: Optional[float]) -> Tuple[bool, str]:
    """Returns (matches, reason). Two areas match if both are missing or
    they are within ±5% of each other."""
    if a is None and b is None:
        return True, 'Area unknown on both'
    if a is None or b is None:
        return False, 'Area missing on one side'
    if a <= 0 or b <= 0:
        return False, 'Invalid area'
    diff = abs(a - b) / max(a, b)
    return diff <= _AREA_TOLERANCE, f'Area within {diff:.1%}'


def _transaction_matches(a: Optional[str], b: Optional[str]) -> bool:
    if not a or not b:
        return False
    return str(a).strip().upper() == str(b).strip().upper()


def _is_hotel(property_type: Optional[str]) -> bool:
    return (property_type or '').strip().upper() == _HOTEL_TYPE


def _evaluate_match(
    *,
    address_a: Optional[str],
    address_b: Optional[str],
    lat_a: Optional[float], lng_a: Optional[float],
    lat_b: Optional[float], lng_b: Optional[float],
    lot_area_a: Optional[float], lot_area_b: Optional[float],
    building_area_a: Optional[float], building_area_b: Optional[float],
    transaction_a: Optional[str], transaction_b: Optional[str],
    type_a: Optional[str], type_b: Optional[str],
) -> Optional[Tuple[float, List[str]]]:
    """Apply all four duplicate rules. Returns (score, reasons) when every
    rule passes, otherwise None."""
    if _is_placeholder(address_a) or _is_placeholder(address_b):
        return None

    # Rule 1: address OR coords
    addr_score = _address_score(address_a, address_b)
    if not _location_matches(addr_score, lat_a, lng_a, lat_b, lng_b):
        return None
    address_reason = (
        f'Address match: {addr_score:.0%}'
        if addr_score >= _ADDRESS_THRESHOLD
        else 'Same GPS location (<30m)'
    )

    # Rule 2: lot area
    lot_ok, lot_reason = _area_matches(lot_area_a, lot_area_b)
    if not lot_ok:
        return None

    # Rule 3: transaction type
    if not _transaction_matches(transaction_a, transaction_b):
        return None

    # Rule 4: hotels only — building/floor area must also match
    hotel_check = _is_hotel(type_a) or _is_hotel(type_b)
    reasons = [address_reason, f'Same lot area ({lot_reason})', f'Same transaction type ({transaction_a})']
    if hotel_check:
        building_ok, building_reason = _area_matches(building_area_a, building_area_b)
        if not building_ok:
            return None
        reasons.append(f'Hotel: building area matches ({building_reason})')

    # Composite score: weight address text similarity heavily; cap at 1.0 when
    # coords confirm a sub-30m match even if addresses differ in spelling.
    coord_lock = (
        addr_score < _ADDRESS_THRESHOLD
        and lat_a is not None and lng_a is not None
        and lat_b is not None and lng_b is not None
    )
    score = 1.0 if coord_lock else max(addr_score, _ADDRESS_THRESHOLD)
    return score, reasons


class DuplicateDetectionService:
    """Flags a property as a duplicate when address, lot area, and transaction
    type all match (and, for hotels, building area too). See module docstring
    for the full rule."""

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
        self, candidate: PropertyCreate, properties: List[Property], exclude_id: Optional[int] = None
    ) -> Optional[Tuple[Property, float, List[str]]]:
        if _is_placeholder(candidate.address):
            return None

        best: Optional[Tuple[Property, float, List[str]]] = None
        for prop in properties:
            if exclude_id and prop.id == exclude_id:
                continue
            if not prop.address:
                continue

            evaluation = _evaluate_match(
                address_a=candidate.address,
                address_b=prop.address,
                lat_a=getattr(candidate, 'latitude', None),
                lng_a=getattr(candidate, 'longitude', None),
                lat_b=getattr(prop, 'latitude', None),
                lng_b=getattr(prop, 'longitude', None),
                lot_area_a=getattr(candidate, 'lot_area', None),
                lot_area_b=getattr(prop, 'lot_area', None),
                building_area_a=getattr(candidate, 'building_area', None),
                building_area_b=getattr(prop, 'building_area', None),
                transaction_a=getattr(candidate, 'transaction_status', None) and (
                    getattr(candidate.transaction_status, 'value', candidate.transaction_status)
                ),
                transaction_b=prop.transaction_status.value if prop.transaction_status else None,
                type_a=getattr(candidate, 'property_type', None) and (
                    getattr(candidate.property_type, 'value', candidate.property_type)
                ),
                type_b=prop.property_type.value if prop.property_type else None,
            )
            if evaluation is None:
                continue
            score, reasons = evaluation
            if best is None or score > best[1]:
                best = (prop, score, reasons)
        return best

    async def check_duplicates(
        self,
        property_data: PropertyCreate,
        threshold: float = _ADDRESS_THRESHOLD,
    ) -> List[DuplicateResult]:
        """Return duplicates that match address + lot area + transaction type
        (and building area for hotels). Threshold is unused — kept for
        backwards-compat with existing callers."""
        properties = await self._load_all_properties()
        match = self._find_duplicate(property_data, properties)
        if not match:
            return []
        prop, score, reasons = match
        return [DuplicateResult(
            property_id=prop.id,
            similarity_score=score,
            match_reasons=reasons,
        )]

    async def check_duplicates_by_criteria(
        self, criteria: DuplicateCheckRequest, threshold: float = _ADDRESS_THRESHOLD
    ) -> List[DuplicateResult]:
        """Apply the full duplicate rule when lot area + transaction type are
        provided. Falls back to address-only matching when they are missing."""
        if not criteria.address:
            return []

        properties = await self._load_all_properties()
        full_rule = (
            criteria.lot_area is not None
            and criteria.transaction_status is not None
        )

        best: Optional[Tuple[Property, float, List[str]]] = None
        for prop in properties:
            if not prop.address:
                continue
            if full_rule:
                evaluation = _evaluate_match(
                    address_a=criteria.address,
                    address_b=prop.address,
                    lat_a=criteria.latitude, lng_a=criteria.longitude,
                    lat_b=prop.latitude, lng_b=prop.longitude,
                    lot_area_a=criteria.lot_area, lot_area_b=prop.lot_area,
                    building_area_a=criteria.building_area, building_area_b=prop.building_area,
                    transaction_a=criteria.transaction_status,
                    transaction_b=prop.transaction_status.value if prop.transaction_status else None,
                    type_a=criteria.property_type,
                    type_b=prop.property_type.value if prop.property_type else None,
                )
                if evaluation is None:
                    continue
                score, reasons = evaluation
            else:
                score = _address_score(criteria.address, prop.address)
                if score < _ADDRESS_THRESHOLD:
                    continue
                reasons = [f'Address match: {score:.0%} (lot area / transaction type not provided)']

            if best is None or score > best[1]:
                best = (prop, score, reasons)

        if not best:
            return []
        prop, score, reasons = best
        return [DuplicateResult(
            property_id=prop.id,
            similarity_score=score,
            match_reasons=reasons,
        )]

    async def calculate_similarity_score(
        self, prop1: Property, prop2: Property
    ) -> float:
        """Return composite duplicate score between two stored properties.
        Returns 0 when the properties don't satisfy all duplicate rules."""
        if not prop1.address or not prop2.address:
            return 0.0
        evaluation = _evaluate_match(
            address_a=prop1.address,
            address_b=prop2.address,
            lat_a=prop1.latitude, lng_a=prop1.longitude,
            lat_b=prop2.latitude, lng_b=prop2.longitude,
            lot_area_a=prop1.lot_area, lot_area_b=prop2.lot_area,
            building_area_a=prop1.building_area, building_area_b=prop2.building_area,
            transaction_a=prop1.transaction_status.value if prop1.transaction_status else None,
            transaction_b=prop2.transaction_status.value if prop2.transaction_status else None,
            type_a=prop1.property_type.value if prop1.property_type else None,
            type_b=prop2.property_type.value if prop2.property_type else None,
        )
        return evaluation[0] if evaluation else 0.0

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
        """Check for duplicates and notify when a strong match is found."""
        duplicates = await self.check_duplicates(property_data, threshold)

        if duplicates:
            from app.services.notification import NotificationService
            notification_service = NotificationService(self.db)

            for duplicate in duplicates:
                # Notify on every confirmed duplicate now — the rule already
                # demands address + lot area + transaction (+ building area for
                # hotels), so a hit is high-confidence by construction.
                await notification_service.create_duplicate_notification(
                    user_id=user_id,
                    property_id=None,
                    duplicate_property_id=duplicate.property_id,
                    similarity_score=duplicate.similarity_score,
                    match_reasons=duplicate.match_reasons,
                )

        return duplicates

    async def notify_staff_of_duplicate(
        self,
        *,
        new_property_id: int,
        new_property_name: str,
        original_property_id: int,
        original_property_name: str,
        submitter_name: str,
        match_reasons: List[str],
        similarity_score: Optional[float] = None,
        proceeded_despite_warning: bool = True,
    ) -> int:
        """In-app-only fan-out to every ADMIN and BDD_USER. Returns count
        of notifications created."""
        from app.models.notification import NotificationType
        from app.schemas.notification import NotificationCreate
        from app.services.notification import NotificationService

        result = await self.db.execute(
            select(User.id).where(User.role.in_([UserRole.ADMIN, UserRole.BDD_USER]))
        )
        staff_ids = [row[0] for row in result.all()]
        if not staff_ids:
            return 0

        reasons_text = ', '.join(match_reasons) if match_reasons else 'rule match'
        score_pct = f"{similarity_score * 100:.0f}%" if similarity_score is not None else 'high'
        action = (
            'submitter chose to proceed despite the warning'
            if proceeded_despite_warning
            else 'auto-detected during submission'
        )
        message = (
            f"Property '{new_property_name}' (ID #{new_property_id}) submitted by "
            f"{submitter_name} was flagged as a duplicate of '{original_property_name}' "
            f"(ID #{original_property_id}) — {action}. "
            f"Match: {score_pct}. Reasons: {reasons_text}."
        )

        notification_service = NotificationService(self.db)
        count = 0
        for staff_id in staff_ids:
            try:
                await notification_service.create_notification(
                    NotificationCreate(
                        user_id=staff_id,
                        notification_type=NotificationType.DUPLICATE_DETECTED,
                        title='Duplicate Property Submitted',
                        message=message,
                        property_id=new_property_id,
                        duplicate_property_id=original_property_id,
                    ),
                    send_email=False,   # in-app only per product decision
                    send_realtime=True, # but still push via websocket
                )
                count += 1
            except Exception as e:
                # Don't let one bad notification block the rest
                print(f"⚠️  Failed to notify staff user {staff_id} of duplicate: {e}")
        return count
