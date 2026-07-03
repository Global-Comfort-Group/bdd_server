"""
Local filesystem storage service for BDD Property Tracker.

Drop-in replacement for OSSService (app.services.oss_service) that keeps files
on the local infra server instead of a third-party object store. It implements
the same public interface so all existing call sites work unchanged:

    upload_file / delete_file / get_file_info / file_exists /
    download_file_content / object_key_from_url / generate_signed_url

Files are stored under ``settings.UPLOAD_DIRECTORY/<object_key>`` and served by
the backend route ``GET /api/v1/files/{object_key}`` (see app/api/v1/files.py).
Access is gated by an HMAC signature (see ``generate_signed_url`` /
``verify_signature``) so the security model matches the private-bucket + signed
temporary URL behaviour of the OSS backend.
"""
import hashlib
import hmac
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from fastapi import HTTPException, UploadFile

from app.core.config import settings

# Path prefix (relative, same-origin) under which files are served.
FILES_URL_PREFIX = f"{settings.API_V1_PREFIX}/files"


class LocalStorageService:
    """Store and serve uploaded files from the local filesystem."""

    def __init__(self):
        self.base_dir = Path(settings.UPLOAD_DIRECTORY).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ paths
    def _abs_path(self, object_key: str) -> Path:
        """Resolve an object_key to an absolute path, guarding against escapes."""
        # Normalise and reject traversal outside the base dir.
        candidate = (self.base_dir / object_key).resolve()
        if not str(candidate).startswith(str(self.base_dir) + os.sep) and candidate != self.base_dir:
            raise HTTPException(status_code=400, detail="Invalid object key")
        return candidate

    def _get_public_url(self, object_key: str) -> str:
        """Stable (unsigned) reference stored in the DB as file_url."""
        return f"{FILES_URL_PREFIX}/{object_key}"

    # --------------------------------------------------------------- signing
    def _sign(self, object_key: str, expires: int) -> str:
        msg = f"{object_key}:{expires}".encode()
        return hmac.new(settings.SECRET_KEY.encode(), msg, hashlib.sha256).hexdigest()

    def verify_signature(self, object_key: str, expires: int, sig: str) -> bool:
        """Validate a signed URL: correct signature and not expired."""
        if not sig or not expires:
            return False
        if int(expires) < int(time.time()):
            return False
        expected = self._sign(object_key, int(expires))
        return hmac.compare_digest(expected, sig)

    def generate_signed_url(
        self, object_key: str, expires: int = 3600, method: str = "GET"
    ) -> str:
        """Return a temporary signed URL for browser/download access."""
        expiry_ts = int(time.time()) + int(expires)
        sig = self._sign(object_key, expiry_ts)
        return f"{FILES_URL_PREFIX}/{object_key}?expires={expiry_ts}&sig={sig}"

    # ---------------------------------------------------------------- upload
    async def upload_file(
        self,
        file: UploadFile,
        subfolder: str = "uploads",
        custom_filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save an UploadFile to local disk, returning OSS-compatible metadata."""
        try:
            if file.size and file.size > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE} bytes",
                )

            original_filename = file.filename or "file"
            file_extension = (
                original_filename.rsplit(".", 1)[-1] if "." in original_filename else ""
            )

            if custom_filename:
                filename = custom_filename
            else:
                filename = f"{uuid.uuid4()}"
                if file_extension:
                    filename = f"{filename}.{file_extension}"

            object_key = f"{subfolder}/{filename}"
            dest = self._abs_path(object_key)
            dest.parent.mkdir(parents=True, exist_ok=True)

            # Stream to disk in chunks to avoid loading large files into memory.
            size = 0
            hasher = hashlib.md5()
            await file.seek(0)
            with open(dest, "wb") as out:
                while True:
                    chunk = await file.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > settings.MAX_FILE_SIZE:
                        out.close()
                        dest.unlink(missing_ok=True)
                        raise HTTPException(
                            status_code=413,
                            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE} bytes",
                        )
                    hasher.update(chunk)
                    out.write(chunk)
            await file.seek(0)

            content_type = file.content_type or "application/octet-stream"
            public_url = self._get_public_url(object_key)

            return {
                "object_key": object_key,
                "url": public_url,
                "secure_url": public_url,
                "file_size": size,
                "mime_type": content_type,
                "original_filename": original_filename,
                "etag": hasher.hexdigest(),
                "request_id": "",
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    # ---------------------------------------------------------------- delete
    def delete_file(self, object_key: str) -> Dict[str, Any]:
        try:
            path = self._abs_path(object_key)
            if path.exists():
                path.unlink()
            return {"result": "ok", "request_id": ""}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Local deletion failed: {str(e)}")

    # ------------------------------------------------------------------ info
    def get_file_info(self, object_key: str) -> Dict[str, Any]:
        path = self._abs_path(object_key)
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {object_key}")
        stat = path.stat()
        return {
            "object_key": object_key,
            "size": stat.st_size,
            "content_type": None,
            "etag": "",
            "last_modified": stat.st_mtime,
            "url": self._get_public_url(object_key),
        }

    def file_exists(self, object_key: str) -> bool:
        try:
            return self._abs_path(object_key).exists()
        except HTTPException:
            return False

    def download_file_content(self, object_key: str) -> bytes:
        path = self._abs_path(object_key)
        if not path.exists():
            raise HTTPException(
                status_code=404, detail=f"File not found: {object_key}"
            )
        try:
            return path.read_bytes()
        except Exception as e:
            raise HTTPException(
                status_code=502, detail=f"Local read failed for {object_key}: {str(e)}"
            )

    # ------------------------------------------------------------- url parse
    def object_key_from_url(self, file_url: str) -> Optional[str]:
        """Extract object_key from a stored file_url.

        Handles the local URL scheme (``.../api/v1/files/<key>``) for both
        relative and absolute forms, and legacy Alibaba OSS URLs so historical
        rows that were migrated (or not yet migrated) still resolve.
        """
        if not file_url:
            return None

        # Local scheme: strip everything up to and including the files prefix.
        path = urlparse(file_url).path if "://" in file_url else file_url
        marker = f"{FILES_URL_PREFIX}/"
        idx = path.find(marker)
        if idx != -1:
            key = path[idx + len(marker):]
            return key.split("?")[0] or None

        # Legacy OSS URLs: https://{bucket}.{endpoint}/{key} or path-style.
        bucket = settings.OSS_BUCKET_NAME
        for prefix in (
            f"https://{bucket}.{settings.OSS_ENDPOINT}/",
            f"https://{bucket}.{settings.OSS_ENDPOINT.replace('-internal', '')}/",
        ):
            if file_url.startswith(prefix):
                return file_url[len(prefix):].split("?")[0] or None
        return None


# Lazy singleton
_local_storage_service: Optional[LocalStorageService] = None


def get_local_storage_service() -> LocalStorageService:
    global _local_storage_service
    if _local_storage_service is None:
        _local_storage_service = LocalStorageService()
    return _local_storage_service
