"""
Alibaba Cloud OSS integration service for file uploads and management
"""
import uuid
from typing import Dict, Any, Optional
from fastapi import HTTPException, UploadFile

import oss2
from oss2.exceptions import OssError

from app.core.config import settings


class OSSService:
    """Service for handling Alibaba Cloud OSS file uploads and management"""

    def __init__(self):
        """Initialize OSS configuration"""
        if not settings.OSS_ACCESS_KEY_ID or not settings.OSS_ACCESS_KEY_SECRET:
            raise ValueError("OSS_ACCESS_KEY_ID and OSS_ACCESS_KEY_SECRET must be configured")

        self.auth = oss2.Auth(
            settings.OSS_ACCESS_KEY_ID,
            settings.OSS_ACCESS_KEY_SECRET
        )

        # Determine if using internal endpoint (for ECS deployment)
        endpoint = settings.OSS_ENDPOINT
        is_internal = 'internal' in endpoint.lower()

        self.bucket = oss2.Bucket(
            self.auth,
            f"https://{endpoint}",
            settings.OSS_BUCKET_NAME
        )

        # Public endpoint for generating accessible URLs
        # If using internal endpoint, construct the public endpoint
        if is_internal:
            self.public_endpoint = endpoint.replace('-internal', '')
        else:
            self.public_endpoint = endpoint

        # Create a public bucket instance for generating signed URLs accessible from browsers
        self.public_bucket = oss2.Bucket(
            self.auth,
            f"https://{self.public_endpoint}",
            settings.OSS_BUCKET_NAME
        )

    def _get_public_url(self, object_key: str) -> str:
        """Generate public URL for an object"""
        return f"https://{settings.OSS_BUCKET_NAME}.{self.public_endpoint}/{object_key}"

    async def upload_file(
        self,
        file: UploadFile,
        subfolder: str = "uploads",
        custom_filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload file to Alibaba Cloud OSS

        Args:
            file: FastAPI UploadFile object
            subfolder: Folder path within the bucket
            custom_filename: Custom filename (optional, will generate UUID if not provided)

        Returns:
            Dict with upload result including URL and metadata
        """
        try:
            # Validate file size (10MB limit)
            if file.size and file.size > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE} bytes"
                )

            # Read file content
            file_content = await file.read()

            # Generate unique filename
            original_filename = file.filename or "file"
            file_extension = original_filename.rsplit('.', 1)[-1] if '.' in original_filename else ''

            if custom_filename:
                filename = custom_filename
            else:
                filename = f"{uuid.uuid4()}"
                if file_extension:
                    filename = f"{filename}.{file_extension}"

            # Build object key (path in bucket)
            object_key = f"{subfolder}/{filename}"

            # Get content type
            content_type = file.content_type or "application/octet-stream"

            # Upload to OSS
            result = self.bucket.put_object(
                object_key,
                file_content,
                headers={
                    'Content-Type': content_type,
                    'x-oss-storage-class': 'Standard'
                }
            )

            # Reset file position for potential reuse
            await file.seek(0)

            # Generate public URL
            public_url = self._get_public_url(object_key)

            return {
                "object_key": object_key,
                "url": public_url,
                "secure_url": public_url,  # OSS URLs are always HTTPS
                "file_size": len(file_content),
                "mime_type": content_type,
                "original_filename": original_filename,
                "etag": result.etag,
                "request_id": result.request_id
            }

        except OssError as e:
            raise HTTPException(
                status_code=400,
                detail=f"OSS upload failed: {str(e)}"
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"File upload failed: {str(e)}"
            )

    def delete_file(self, object_key: str) -> Dict[str, Any]:
        """
        Delete file from OSS

        Args:
            object_key: Object key (path) in the bucket

        Returns:
            Deletion result
        """
        try:
            result = self.bucket.delete_object(object_key)
            return {
                "result": "ok",
                "request_id": result.request_id
            }
        except OssError as e:
            raise HTTPException(
                status_code=400,
                detail=f"OSS deletion failed: {str(e)}"
            )

    def get_file_info(self, object_key: str) -> Dict[str, Any]:
        """
        Get file information from OSS

        Args:
            object_key: Object key (path) in the bucket

        Returns:
            File information
        """
        try:
            meta = self.bucket.get_object_meta(object_key)
            return {
                "object_key": object_key,
                "size": meta.content_length,
                "content_type": meta.content_type,
                "etag": meta.etag,
                "last_modified": meta.last_modified,
                "url": self._get_public_url(object_key)
            }
        except oss2.exceptions.NoSuchKey:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {object_key}"
            )
        except OssError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get file info: {str(e)}"
            )

    def file_exists(self, object_key: str) -> bool:
        """Check if a file exists in OSS"""
        try:
            return self.bucket.object_exists(object_key)
        except OssError:
            return False

    def generate_signed_url(
        self,
        object_key: str,
        expires: int = 3600,
        method: str = 'GET'
    ) -> str:
        """
        Generate a signed URL for temporary access

        Args:
            object_key: Object key (path) in the bucket
            expires: URL expiration time in seconds (default 1 hour)
            method: HTTP method (GET, PUT, etc.)

        Returns:
            Signed URL
        """
        try:
            return self.public_bucket.sign_url(method, object_key, expires)
        except OssError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to generate signed URL: {str(e)}"
            )


# Lazy initialization - only create instance when needed
_oss_service: Optional[OSSService] = None


def get_oss_service() -> OSSService:
    """Get or create OSS service instance"""
    global _oss_service
    if _oss_service is None:
        _oss_service = OSSService()
    return _oss_service
