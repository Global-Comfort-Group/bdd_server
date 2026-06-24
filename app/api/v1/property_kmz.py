"""
Per-property KMZ (Google Earth) endpoints.

Upload a KMZ against a property; the archive is stored in OSS and its placemarks
(buildings, infrastructure, pins) are parsed into a GeoJSON FeatureCollection
cached in the database so the Property View can render them directly.
"""
import hashlib
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.database import get_async_session
from app.models.property import Property
from app.models.property_kmz import PropertyKMZ
from app.models.user import User, UserRole
from app.schemas.property_kmz import PropertyKMZFeatures, PropertyKMZRead
from app.services.file_storage import file_storage_service
from app.services.kmz_parser import KMZParseError, parse_kmz
from app.services.oss_service import get_oss_service

router = APIRouter(tags=["property-kmz"])


def _can_modify_property(user: User, property_obj: Property) -> bool:
    """Submitter, BDD users, and admins may add/remove a property's KMZ files."""
    return (
        user.role in (UserRole.BDD_USER, UserRole.ADMIN)
        or property_obj.submitted_by_id == user.id
    )


async def _get_property_or_404(db: AsyncSession, property_id: int) -> Property:
    result = await db.execute(select(Property).where(Property.id == property_id))
    property_obj = result.scalar_one_or_none()
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    return property_obj


@router.post("/properties/{property_id}/kmz", response_model=PropertyKMZRead, status_code=201)
async def upload_property_kmz(
    property_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Upload a KMZ for a property: store the archive in OSS and cache its
    parsed GeoJSON. Submitter, BDD users, and admins only."""
    property_obj = await _get_property_or_404(db, property_id)

    if not _can_modify_property(current_user, property_obj):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to add KMZ files to this property",
        )

    if not (file.filename or "").lower().endswith(".kmz"):
        raise HTTPException(status_code=422, detail="File must be a .kmz archive")

    content = await file.read()
    try:
        geojson = parse_kmz(content)
    except KMZParseError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid KMZ file: {exc}")

    file_sha256 = hashlib.sha256(content).hexdigest()

    # Upload the raw archive to OSS (upload_file re-reads the stream).
    await file.seek(0)
    oss_service = get_oss_service()
    upload_result = await oss_service.upload_file(
        file=file,
        subfolder=f"property_{property_id}/kmz",
    )

    kmz = PropertyKMZ(
        property_id=property_id,
        filename=file.filename,
        oss_object_key=upload_result["object_key"],
        file_url=upload_result["secure_url"],
        file_size=upload_result["file_size"],
        file_sha256=file_sha256,
        parsed_data=geojson,
        feature_count=len(geojson.get("features", [])),
        uploaded_by=current_user.id,
    )

    try:
        db.add(kmz)
        await db.commit()
        await db.refresh(kmz)
    except Exception as exc:
        await db.rollback()
        # Best-effort cleanup of the orphaned OSS object.
        try:
            await file_storage_service.delete_file(upload_result["object_key"])
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to save KMZ: {exc}")

    return kmz


@router.get("/properties/{property_id}/kmz", response_model=List[PropertyKMZRead])
async def list_property_kmz(
    property_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """List KMZ files for a property (metadata only, newest first)."""
    await _get_property_or_404(db, property_id)
    result = await db.execute(
        select(PropertyKMZ)
        .where(PropertyKMZ.property_id == property_id)
        .order_by(PropertyKMZ.created_at.desc())
    )
    return result.scalars().all()


async def _get_kmz_or_404(db: AsyncSession, kmz_id: int) -> PropertyKMZ:
    kmz = await db.get(PropertyKMZ, kmz_id)
    if not kmz:
        raise HTTPException(status_code=404, detail="KMZ file not found")
    return kmz


@router.get("/kmz/{kmz_id}/features", response_model=PropertyKMZFeatures)
async def get_kmz_features(
    kmz_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Return the parsed GeoJSON FeatureCollection for rendering on the map."""
    kmz = await _get_kmz_or_404(db, kmz_id)
    return PropertyKMZFeatures(
        id=kmz.id,
        property_id=kmz.property_id,
        filename=kmz.filename,
        feature_count=kmz.feature_count,
        geojson=kmz.parsed_data,
    )


@router.get("/kmz/{kmz_id}/download")
async def download_kmz(
    kmz_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Return a short-lived signed URL to download the original KMZ archive."""
    kmz = await _get_kmz_or_404(db, kmz_id)
    signed_url = get_oss_service().generate_signed_url(kmz.oss_object_key, expires=3600)
    return {"download_url": signed_url, "filename": kmz.filename}


@router.delete("/kmz/{kmz_id}")
async def delete_kmz(
    kmz_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Delete a KMZ file (OSS object + DB record). Submitter, BDD users, and
    admins only."""
    kmz = await _get_kmz_or_404(db, kmz_id)
    property_obj = await _get_property_or_404(db, kmz.property_id)

    if not _can_modify_property(current_user, property_obj):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to delete this KMZ file",
        )

    await file_storage_service.delete_file(kmz.oss_object_key)
    await db.delete(kmz)
    await db.commit()
    return {"message": "KMZ file deleted successfully"}
