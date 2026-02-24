"""
File storage service using Alibaba Cloud OSS for BDD Property Tracker
"""
import uuid
from typing import Dict, Any, Optional
from pathlib import Path
from fastapi import UploadFile, HTTPException

from app.core.config import settings
from app.services.oss_service import get_oss_service


class FileStorageService:
    """Service for handling file uploads using Alibaba Cloud OSS."""

    def __init__(self):
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_types = {
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/plain', 'text/csv'
        }

    async def save_file(self, file: UploadFile, subfolder: str = "properties") -> Dict[str, Any]:
        """
        Save uploaded file to Alibaba Cloud OSS.

        Args:
            file: The uploaded file
            subfolder: Subfolder to organize files in OSS bucket

        Returns:
            Dict with file information including URLs and metadata
        """
        # Validate file size
        if file.size and file.size > self.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum allowed size of {self.max_file_size} bytes"
            )

        # Validate file type
        if not self.validate_file_type(file):
            raise HTTPException(
                status_code=422,
                detail=f"File type {file.content_type} is not allowed"
            )

        try:
            # Get OSS service instance
            oss_service = get_oss_service()

            # Upload to OSS
            result = await oss_service.upload_file(
                file=file,
                subfolder=subfolder
            )

            return result

        except HTTPException:
            # Re-raise HTTPException from oss_service
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload file: {str(e)}"
            )

    async def delete_file(self, object_key: str) -> bool:
        """
        Delete a file from OSS.

        Args:
            object_key: OSS object key (path)

        Returns:
            True if successful, False otherwise
        """
        try:
            oss_service = get_oss_service()
            result = oss_service.delete_file(object_key)
            return result.get("result") == "ok"
        except HTTPException:
            return False
        except Exception:
            return False

    def get_file_url(self, object_key: str) -> str:
        """
        Get public URL for a file in OSS.

        Args:
            object_key: OSS object key (path)

        Returns:
            Public URL
        """
        try:
            oss_service = get_oss_service()
            info = oss_service.get_file_info(object_key)
            return info["url"]
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to generate URL: {str(e)}"
            )

    def get_signed_url(self, object_key: str, expires: int = 3600) -> str:
        """
        Generate signed URL for temporary access.

        Args:
            object_key: OSS object key (path)
            expires: URL expiration time in seconds

        Returns:
            Signed URL
        """
        try:
            oss_service = get_oss_service()
            return oss_service.generate_signed_url(object_key, expires)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to generate signed URL: {str(e)}"
            )

    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename."""
        if not filename:
            return ""
        return Path(filename).suffix.lower()

    def validate_file_type(self, file: UploadFile) -> bool:
        """Validate if file type is allowed, checking content-type and file extension."""
        # Primary check: content-type header
        if file.content_type in self.allowed_types:
            return True
        # Fallback: guess from extension when browser omits content-type (e.g. WebP on some systems)
        ext = Path(file.filename or '').suffix.lower()
        extension_types = {
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
            '.png': 'image/png', '.gif': 'image/gif', '.webp': 'image/webp',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.txt': 'text/plain', '.csv': 'text/csv',
        }
        guessed = extension_types.get(ext)
        return guessed in self.allowed_types if guessed else False

    def get_file_info(self, object_key: str) -> Dict[str, Any]:
        """
        Get file information from OSS.

        Args:
            object_key: OSS object key (path)

        Returns:
            File information
        """
        try:
            oss_service = get_oss_service()
            return oss_service.get_file_info(object_key)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get file info: {str(e)}"
            )


# Global instance
file_storage_service = FileStorageService()
