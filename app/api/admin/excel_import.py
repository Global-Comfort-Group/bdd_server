"""
Admin Portal — Excel Property Import Endpoints

An Excel row is a referral LEAD, not a property. The sheet has no price,
zoning, property type, coordinates, title or photos — all of which `properties`
requires. So importing does not create properties; it fills a review queue.

  1. POST /admin/properties/import/preview            upload, get parsed rows + token
  2. POST /admin/properties/import/confirm            stage selected rows into the queue
  3. GET  /admin/properties/import/queue              list staged leads
  4. POST /admin/properties/import/queue/{id}/promote supply the missing fields -> Property
  5. POST /admin/properties/import/queue/{id}/discard drop a lead

Nothing between steps 2 and 4 invents a value: a field the sheet lacks stays
NULL until a human supplies it at promotion.
"""
import uuid
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.models.enums import TransactionStatus
from app.models.property_import import (
    IMPORT_DISCARDED,
    IMPORT_PENDING,
    IMPORT_PROMOTED,
    PropertyImport,
)
from app.models.user import User
from app.api.admin.admin_auth import current_admin_user
from app.services.excel_import_service import parse_excel_properties
from app.services.import_dedupe import flag_duplicates
from app.services import property_import_service as staging
from app.schemas.property import (
    ExcelParseResponse,
    ExcelPropertyPreviewRow,
    ExcelImportConfirmRequest,
    ExcelImportResult,
    PromoteImportRequest,
    PropertyImportListResponse,
    PropertyImportRead,
    PromotionResult,
)

router = APIRouter(prefix="/properties/import", tags=["admin-excel-import"])

# ── In-memory cache ──────────────────────────────────────────────────────────
# Stores parsed rows keyed by import_token.
# Each entry: {"rows": list[dict], "expires_at": float (unix timestamp)}
_import_cache: Dict[str, Any] = {}

_TOKEN_TTL_SECONDS = 600  # 10 minutes


def _evict_expired() -> None:
    """Remove expired tokens from the cache."""
    now = time.time()
    expired = [k for k, v in _import_cache.items() if v["expires_at"] < now]
    for k in expired:
        del _import_cache[k]


def _missing_required(record: PropertyImport) -> List[str]:
    """Fields a human must supply before this lead can become a Property.

    Nothing is outstanding once the lead has left the queue — a promoted row's
    values were supplied at promotion, and a discarded one is not going to be
    promoted.
    """
    if record.review_status != IMPORT_PENDING:
        return []
    missing = ["price", "property_type", "zoning_classification"]
    if record.lot_area is None:
        missing.append("lot_area")
    derived = staging.derived_transaction_status(record)
    if derived is None:
        missing.append("transaction_status")
    elif derived == TransactionStatus.SL:
        # A sheet row carrying BOTH a lease and a sale figure derives Sale &
        # Lease, and the property schema requires a lease price for that — so
        # say so up front rather than failing at submit.
        missing.append("lease_price")
    return missing


def _to_read(record: PropertyImport) -> PropertyImportRead:
    payload = PropertyImportRead.model_validate(record)
    payload.missing_required = _missing_required(record)
    return payload


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/preview", response_model=ExcelParseResponse)
async def preview_excel_import(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_admin_user),
):
    """
    Upload a BDD monthly Excel file and get a preview of all parseable property rows.

    Returns an import_token (valid for 10 minutes) along with the parsed rows.
    Pass the token to /confirm to add the selected rows to the review queue.
    """
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .xlsx or .xls files are accepted.",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    try:
        raw_rows = parse_excel_properties(file_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse Excel file: {str(e)}",
        )

    if not raw_rows:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No property rows found in the uploaded file. "
                   "Make sure it follows the BDD monthly format.",
        )

    # Flag against real properties AND leads still sitting in the queue.
    existing = await staging.existing_keys_and_labels(db)
    raw_rows = flag_duplicates(raw_rows, existing)
    duplicate_count = sum(1 for r in raw_rows if r.get("duplicate_kind"))

    _evict_expired()
    import_token = str(uuid.uuid4())
    _import_cache[import_token] = {
        "rows": raw_rows,
        "source_file": file.filename,
        "expires_at": time.time() + _TOKEN_TTL_SECONDS,
    }

    preview_rows = [ExcelPropertyPreviewRow(**row) for row in raw_rows]

    return ExcelParseResponse(
        import_token=import_token,
        total_rows=len(preview_rows),
        duplicate_count=duplicate_count,
        rows=preview_rows,
    )


@router.post("/confirm", response_model=ExcelImportResult)
async def confirm_excel_import(
    body: ExcelImportConfirmRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_admin_user),
):
    """
    Add the selected rows to the review queue.

    This does NOT create properties. Rows land in `property_imports` with every
    sheet-absent value left NULL; they become properties only via /promote.
    """
    _evict_expired()

    cached = _import_cache.get(body.import_token)
    if not cached:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import token not found or expired. Please re-upload the file.",
        )

    if time.time() > cached["expires_at"]:
        del _import_cache[body.import_token]
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Import token has expired. Please re-upload the file.",
        )

    if not body.row_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No rows selected for import.",
        )

    selected_ids = set(body.row_ids)
    all_rows = cached["rows"]
    selected_rows = [r for r in all_rows if r["row_id"] in selected_ids]
    not_found = len(body.row_ids) - len(selected_rows)

    staged_count, duplicate_skipped, errors = await staging.stage_rows(
        db,
        rows=selected_rows,
        user_id=current_user.id,
        source_file=cached.get("source_file"),
    )

    del _import_cache[body.import_token]

    return ExcelImportResult(
        staged_count=staged_count,
        skipped_count=not_found + len(errors) + duplicate_skipped,
        duplicate_skipped_count=duplicate_skipped,
        errors=errors,
    )


@router.get("/queue", response_model=PropertyImportListResponse)
async def list_import_queue(
    review_status: Optional[str] = Query(None, description="PENDING / PROMOTED / DISCARDED"),
    search: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_admin_user),
):
    """List staged leads, newest first."""
    counts = dict(
        (
            await db.execute(
                select(PropertyImport.review_status, func.count())
                .group_by(PropertyImport.review_status)
            )
        ).all()
    )

    stmt = select(PropertyImport)
    if review_status:
        stmt = stmt.where(PropertyImport.review_status == review_status.upper())
    if search:
        like = f"%{search}%"
        stmt = stmt.where(PropertyImport.name.ilike(like) | PropertyImport.address.ilike(like))
    stmt = stmt.order_by(PropertyImport.id.desc()).limit(limit).offset(offset)

    records = (await db.execute(stmt)).scalars().all()

    return PropertyImportListResponse(
        total=sum(counts.values()),
        pending=counts.get(IMPORT_PENDING, 0),
        promoted=counts.get(IMPORT_PROMOTED, 0),
        discarded=counts.get(IMPORT_DISCARDED, 0),
        items=[_to_read(r) for r in records],
    )


@router.post("/queue/{import_id}/promote", response_model=PromotionResult)
async def promote_import(
    import_id: int,
    body: PromoteImportRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_admin_user),
):
    """Turn a staged lead into a real Property using admin-supplied values."""
    record = await db.get(PropertyImport, import_id)
    if not record:
        raise HTTPException(status_code=404, detail="Import row not found.")

    overrides = body.model_dump(exclude_unset=True)
    try:
        prop = await staging.promote(db, record, overrides, current_user.id)
    except staging.PromotionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    await db.refresh(record)
    return PromotionResult(
        property_id=prop.id,
        property_name=prop.name,
        import_row=_to_read(record),
    )


@router.post("/queue/{import_id}/discard", response_model=PropertyImportRead)
async def discard_import(
    import_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_admin_user),
):
    """Drop a lead from the queue. Reversible — the row is kept, not deleted."""
    record = await db.get(PropertyImport, import_id)
    if not record:
        raise HTTPException(status_code=404, detail="Import row not found.")
    if record.review_status == IMPORT_PROMOTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This lead was already promoted to a property.",
        )
    record.review_status = IMPORT_DISCARDED
    await db.commit()
    await db.refresh(record)
    return _to_read(record)
