"""
S3-compatible object storage service (Railway buckets, MinIO, AWS S3, ...).

Mirrors the interface of `OSSService` exactly, so `get_oss_service()` can hand
back either one and every call site works unchanged. Which backend is used is
decided by configuration alone — see `app.services.oss_service.get_oss_service`.

Stored URLs use the virtual-hosted form `https://{bucket}.{host}/{key}`, matching
the shape OSS produces, so `object_key_from_url` keeps working across backends.
Buckets are typically private; callers already request a signed URL at read time
rather than serving the stored URL directly.
"""
import uuid
from typing import Dict, Any, Optional
from urllib.parse import urlparse

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, UploadFile

from app.core.config import settings


class S3Service:
    """Service for handling S3-compatible file uploads and management"""

    def __init__(self):
        if not settings.S3_ACCESS_KEY_ID or not settings.S3_SECRET_ACCESS_KEY:
            raise ValueError("S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY must be configured")
        if not settings.S3_BUCKET_NAME or not settings.S3_ENDPOINT_URL:
            raise ValueError("S3_BUCKET_NAME and S3_ENDPOINT_URL must be configured")

        self.bucket_name = settings.S3_BUCKET_NAME
        self.endpoint_url = settings.S3_ENDPOINT_URL.rstrip('/')
        self.host = urlparse(self.endpoint_url).netloc

        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION,
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": settings.S3_ADDRESSING_STYLE},
            ),
        )

    def _get_public_url(self, object_key: str) -> str:
        """Canonical stored URL for an object."""
        if settings.S3_ADDRESSING_STYLE == "path":
            return f"{self.endpoint_url}/{self.bucket_name}/{object_key}"
        return f"https://{self.bucket_name}.{self.host}/{object_key}"

    async def upload_file(
        self,
        file: UploadFile,
        subfolder: str = "uploads",
        custom_filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload file to S3-compatible storage.

        Args:
            file: FastAPI UploadFile object
            subfolder: Folder path within the bucket
            custom_filename: Custom filename (optional, will generate UUID if not provided)

        Returns:
            Dict with upload result including URL and metadata
        """
        try:
            if file.size and file.size > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE} bytes"
                )

            file_content = await file.read()

            original_filename = file.filename or "file"
            file_extension = original_filename.rsplit('.', 1)[-1] if '.' in original_filename else ''

            if custom_filename:
                filename = custom_filename
            else:
                filename = f"{uuid.uuid4()}"
                if file_extension:
                    filename = f"{filename}.{file_extension}"

            object_key = f"{subfolder}/{filename}"
            content_type = file.content_type or "application/octet-stream"

            result = self.client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_content,
                ContentType=content_type,
            )

            # Reset file position for potential reuse
            await file.seek(0)

            public_url = self._get_public_url(object_key)

            return {
                "object_key": object_key,
                "url": public_url,
                "secure_url": public_url,
                "file_size": len(file_content),
                "mime_type": content_type,
                "original_filename": original_filename,
                "etag": (result.get("ETag") or "").strip('"'),
                "request_id": result.get("ResponseMetadata", {}).get("RequestId"),
            }

        except HTTPException:
            raise
        except (ClientError, BotoCoreError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"S3 upload failed: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"File upload failed: {str(e)}"
            )

    def delete_file(self, object_key: str) -> Dict[str, Any]:
        """Delete file from the bucket."""
        try:
            result = self.client.delete_object(Bucket=self.bucket_name, Key=object_key)
            return {
                "result": "ok",
                "request_id": result.get("ResponseMetadata", {}).get("RequestId"),
            }
        except (ClientError, BotoCoreError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"S3 deletion failed: {str(e)}"
            )

    def get_file_info(self, object_key: str) -> Dict[str, Any]:
        """Get object metadata."""
        try:
            meta = self.client.head_object(Bucket=self.bucket_name, Key=object_key)
            last_modified = meta.get("LastModified")
            return {
                "object_key": object_key,
                "size": meta.get("ContentLength"),
                "content_type": meta.get("ContentType"),
                "etag": (meta.get("ETag") or "").strip('"'),
                "last_modified": last_modified.isoformat() if last_modified else None,
                "url": self._get_public_url(object_key),
            }
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") in ("404", "NoSuchKey", "NotFound"):
                raise HTTPException(
                    status_code=404,
                    detail=f"File not found: {object_key}"
                )
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get file info: {str(e)}"
            )
        except BotoCoreError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get file info: {str(e)}"
            )

    def file_exists(self, object_key: str) -> bool:
        """Check if an object exists."""
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except (ClientError, BotoCoreError):
            return False

    def download_file_content(self, object_key: str) -> bytes:
        """Download object bytes with authenticated credentials (works on private buckets)."""
        try:
            obj = self.client.get_object(Bucket=self.bucket_name, Key=object_key)
            return obj["Body"].read()
        except (ClientError, BotoCoreError) as e:
            raise HTTPException(
                status_code=502,
                detail=f"S3 download failed for {object_key}: {str(e)}"
            )

    def object_key_from_url(self, file_url: str) -> Optional[str]:
        """Extract the object key from a stored file URL.
        Accepts virtual-hosted (https://{bucket}.{host}/{key}) and path-style
        (https://{host}/{bucket}/{key}) URLs. Returns None if neither matches."""
        if not file_url:
            return None
        prefix_subdomain = f"https://{self.bucket_name}.{self.host}/"
        if file_url.startswith(prefix_subdomain):
            return file_url[len(prefix_subdomain):]
        prefix_path = f"{self.endpoint_url}/{self.bucket_name}/"
        if file_url.startswith(prefix_path):
            return file_url[len(prefix_path):]
        return None

    def generate_signed_url(
        self,
        object_key: str,
        expires: int = 3600,
        method: str = 'GET'
    ) -> str:
        """Generate a presigned URL for temporary access."""
        operation = {
            "GET": "get_object",
            "PUT": "put_object",
            "DELETE": "delete_object",
        }.get(method.upper(), "get_object")
        try:
            return self.client.generate_presigned_url(
                operation,
                Params={"Bucket": self.bucket_name, "Key": object_key},
                ExpiresIn=expires,
            )
        except (ClientError, BotoCoreError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to generate signed URL: {str(e)}"
            )
