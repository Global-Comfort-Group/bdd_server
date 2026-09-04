"""
Staging and promotion for Excel-imported property leads.

Two steps, deliberately separated:

  * ``stage_rows``   — parsed Excel rows land in ``property_imports``. Nothing
    is invented: a value the sheet does not carry stays NULL.

  * ``promote``      — an admin supplies the fields ``properties`` requires
    (price, property type, zoning) and a real Property is created from the
    staging row plus those values.

This is the only place that knows how to turn sheet data into a Property.
"""
from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence, Tuple

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PropertyStatus, PropertyType, TransactionStatus
from app.models.property import Property
from app.models.property_import import (
    IMPORT_DISCARDED,
    IMPORT_PENDING,
    IMPORT_PROMOTED,
    PropertyImport,
)
from app.schemas.property import PropertyCreate
from app.services.import_dedupe import import_key


def _readable_errors(e: ValidationError) -> str:
    """Turn pydantic's error list into one sentence an admin can act on."""
    parts = []
    for err in e.errors():
        field = ".".join(str(p) for p in err.get("loc", ())) or "value"
        parts.append(f"{field}: {err.get('msg', 'invalid')}")
    return "; ".join(parts)


async def existing_keys_and_labels(
    db: AsyncSession,
) -> List[Tuple[int, Optional[str], Optional[str], str]]:
    """Everything an incoming row could duplicate: real properties, plus
    staging rows still awaiting review. A lead imported last month and not yet
    promoted is still a duplicate for this month's file."""
    props = (await db.execute(select(Property.id, Property.name, Property.address))).all()
    pending = (
        await db.execute(
            select(PropertyImport.id, PropertyImport.name, PropertyImport.address)
            .where(PropertyImport.review_status == IMPORT_PENDING)
        )
    ).all()
    return (
        [(p.id, p.name, p.address, "database") for p in props]
        + [(i.id, i.name, i.address, "import queue") for i in pending]
    )


async def stage_rows(
    db: AsyncSession, rows: Sequence[Dict[str, Any]], user_id: int, source_file: Optional[str]
) -> Tuple[int, int, List[str]]:
    """Insert parsed rows into the staging table.

    Enforces the exact dedupe key against real properties AND pending staging
    rows, so a client that ignores the preview flags still cannot create a
    second copy.

    Returns (staged_count, duplicate_skipped, errors).
    """
    existing = await existing_keys_and_labels(db)
    seen_keys = {import_key(name, address) for _id, name, address, _src in existing}

    staged = 0
    duplicate_skipped = 0
    errors: List[str] = []

    for row in rows:
        try:
            name = (row.get("name") or "").strip()
            address = (row.get("address") or "").strip()
            if not name or not address:
                errors.append(
                    f"Row {row.get('row_id', '?')}: skipped — name or address is empty"
                )
                continue

            key = import_key(name, address)
            if key in seen_keys:
                duplicate_skipped += 1
                continue
            seen_keys.add(key)

            db.add(
                PropertyImport(
                    name=name,
                    address=address,
                    referred_by=row.get("referred_by"),
                    referral_type=row.get("referral_type"),
                    # NULL, not 0.0 — the sheet simply had nothing here.
                    lot_area=row.get("lot_area"),
                    building_area=row.get("building_area"),
                    lease_raw=row.get("lease_raw"),
                    sale_raw=row.get("sale_raw"),
                    status_hint=row.get("status_hint"),
                    sheet_name=row.get("sheet_name"),
                    row_number=row.get("row_number"),
                    source_file=source_file,
                    review_status=IMPORT_PENDING,
                    imported_by_id=user_id,
                )
            )
            staged += 1
        except Exception as e:  # pragma: no cover - defensive
            errors.append(f"Row {row.get('row_id', '?')}: {str(e)}")

    if staged:
        await db.commit()

    return staged, duplicate_skipped, errors


def derived_transaction_status(record: PropertyImport) -> Optional[TransactionStatus]:
    """L / S / SL from which of the Lease and Sale columns were populated.

    Returns None when the sheet said nothing — the caller must then ask rather
    than defaulting to Sale, which is what the old importer did for every row.
    """
    lease = (record.lease_raw or "").strip()
    sale = (record.sale_raw or "").strip()
    if lease and sale:
        return TransactionStatus.SL
    if lease:
        return TransactionStatus.L
    if sale:
        return TransactionStatus.S
    return None


def provenance_note(record: PropertyImport) -> str:
    """What the sheet said, preserved verbatim on the promoted property.

    The lease/sale figures live here rather than in `price` because the column
    mixes per-sqm rates with absolute totals and cannot be trusted as a number.
    """
    notes = []
    if record.referral_type:
        notes.append(f"Referral type: {record.referral_type}")
    if record.sale_raw:
        notes.append(f"Sale (as listed): {record.sale_raw}")
    if record.lease_raw:
        notes.append(f"Lease (as listed): {record.lease_raw}")
    if record.status_hint:
        notes.append(f"Status from sheet: {record.status_hint}")
    if record.sheet_name:
        notes.append(f"Imported from {record.sheet_name}")
    return " | ".join(notes)


class PromotionError(Exception):
    """Raised when a staging row cannot become a Property."""


async def promote(
    db: AsyncSession,
    record: PropertyImport,
    overrides: Dict[str, Any],
    user_id: int,
) -> Property:
    """Create a real Property from a staging row plus admin-supplied values.

    Every field `properties` requires but the sheet lacks must arrive in
    ``overrides``. Nothing is defaulted silently — a missing required value is
    an error, not a guess.
    """
    if record.review_status == IMPORT_PROMOTED:
        raise PromotionError("This row has already been promoted.")
    if record.review_status == IMPORT_DISCARDED:
        raise PromotionError("This row was discarded. Restore it before promoting.")

    # Re-check against real properties at promotion time: time has passed since
    # the import, and someone may have created this property by hand since.
    key = import_key(record.name, record.address)
    props = (await db.execute(select(Property.id, Property.name, Property.address))).all()
    for p in props:
        if import_key(p.name, p.address) == key:
            raise PromotionError(
                f"A property named '{p.name}' already exists at this address (id {p.id})."
            )

    lot_area = overrides.get("lot_area", record.lot_area)
    price = overrides.get("price")
    property_type = overrides.get("property_type")
    zoning = overrides.get("zoning_classification")
    transaction_status = overrides.get("transaction_status") or derived_transaction_status(record)

    missing = [
        label
        for label, value in (
            ("lot_area", lot_area),
            ("price", price),
            ("property_type", property_type),
            ("zoning_classification", zoning),
            ("transaction_status", transaction_status),
        )
        if value is None
    ]
    if missing:
        raise PromotionError(
            "The Excel sheet does not carry these fields — they must be supplied: "
            + ", ".join(missing)
        )

    existing_note = provenance_note(record)
    description = overrides.get("description") or existing_note or None
    if overrides.get("description") and existing_note:
        description = f"{overrides['description']}\n\n{existing_note}"

    payload = {
        "name": overrides.get("name") or record.name,
        "address": overrides.get("address") or record.address,
        "lot_area": lot_area,
        "price": price,
        "property_type": property_type,
        "zoning_classification": zoning,
        "transaction_status": transaction_status,
        "lease_price": overrides.get("lease_price"),
        "building_area": overrides.get("building_area", record.building_area),
        "referred_by": overrides.get("referred_by", record.referred_by),
        "description": description,
        "currency": overrides.get("currency") or "PHP",
        "latitude": overrides.get("latitude"),
        "longitude": overrides.get("longitude"),
        "title_number": overrides.get("title_number"),
        "floors": overrides.get("floors"),
        "parking_slots": overrides.get("parking_slots"),
        "rooms": overrides.get("rooms"),
    }

    # Validate through the SAME schema a manually submitted property uses, so a
    # promoted lead cannot bypass rules the form enforces: price > 0,
    # lot_area > 0, lease_price required for Sale & Lease, and zoning limited
    # to the allowed values. Building the ORM model directly — as this used to —
    # skipped every one of them.
    data = {k: v for k, v in payload.items() if v is not None}
    # lease_price must be passed explicitly even when empty: its validator only
    # runs for a field that is actually supplied, so dropping it as "None" would
    # silently skip the "required for Sale & Lease" rule.
    data["lease_price"] = payload.get("lease_price")

    try:
        validated = PropertyCreate(**data)
    except ValidationError as e:
        raise PromotionError(_readable_errors(e))

    prop = Property(
        **validated.model_dump(exclude_none=True),
        status=PropertyStatus.PROPERTY_SOURCING,
        submitted_by_id=user_id,
        # Marks provenance: this property came from a promoted Excel lead.
        is_imported=True,
    )
    db.add(prop)
    await db.flush()

    record.review_status = IMPORT_PROMOTED
    record.promoted_property_id = prop.id
    await db.commit()
    await db.refresh(prop)
    return prop
