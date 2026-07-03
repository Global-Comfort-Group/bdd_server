"""
Local file serving endpoint.

Serves files stored on the local infra server by LocalStorageService. Access is
gated by the HMAC signature produced by ``generate_signed_url`` so behaviour
matches the private-bucket + temporary-signed-URL model of the OSS backend.

Route: ``GET /api/v1/files/{object_key}?expires=<ts>&sig=<hmac>``
"""
import mimetypes
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.services.local_storage_service import get_local_storage_service

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/{object_key:path}")
async def serve_file(
    object_key: str,
    expires: int = Query(..., description="Unix expiry timestamp"),
    sig: str = Query(..., description="HMAC signature"),
):
    """Serve a locally stored file if the signed URL is valid and unexpired."""
    storage = get_local_storage_service()

    if not storage.verify_signature(object_key, expires, sig):
        raise HTTPException(status_code=403, detail="Invalid or expired signature")

    path: Path = storage._abs_path(object_key)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    media_type, _ = mimetypes.guess_type(str(path))
    filename = path.name
    return FileResponse(
        path,
        media_type=media_type or "application/octet-stream",
        filename=filename,
        content_disposition_type="inline",
    )
